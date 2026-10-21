<?php
declare(strict_types=1);

/**
 * StaxTech AI Assistant API proxy.
 *
 * Configure these environment variables on your hosting server:
 *   AI_API_URL  e.g. the chat-completions endpoint from your AI provider
 *   AI_API_KEY  provider secret key (never commit it to GitHub)
 *   AI_MODEL    provider model name
 *
 * This proxy expects an OpenAI-compatible chat-completions API.
 */
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    header('Allow: POST');
    echo json_encode(['error' => 'Use POST for chat requests.']);
    exit;
}

$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
$host = $_SERVER['HTTP_HOST'] ?? '';
if ($origin !== '' && $host !== '' && parse_url($origin, PHP_URL_HOST) !== $host) {
    http_response_code(403);
    echo json_encode(['error' => 'Origin not allowed.']);
    exit;
}

$apiUrl = getenv('AI_API_URL') ?: '';
$apiKey = getenv('AI_API_KEY') ?: '';
$model = getenv('AI_MODEL') ?: '';

if ($apiUrl === '' || $apiKey === '' || $model === '') {
    http_response_code(503);
    echo json_encode(['error' => 'The AI assistant is not configured yet. Please contact the site administrator.']);
    exit;
}
if (!filter_var($apiUrl, FILTER_VALIDATE_URL) || !in_array(parse_url($apiUrl, PHP_URL_SCHEME), ['https'], true)) {
    http_response_code(500);
    echo json_encode(['error' => 'AI_API_URL must be a valid HTTPS URL.']);
    exit;
}

$raw = file_get_contents('php://input');
$input = json_decode($raw ?: '', true);
if (!is_array($input) || !isset($input['messages']) || !is_array($input['messages'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid request payload.']);
    exit;
}

$messages = [];
$system = 'You are the helpful StaxTech website assistant. Answer clearly and politely. You may help with StaxTech services, internship applications, website navigation, and general questions. For official program details you are unsure about, direct users to https://staxtech.in or info@staxtech.in. Never claim to have completed an action you cannot perform. Do not ask users for passwords, OTPs, payment card details, or secret information. Keep responses concise.';
$messages[] = ['role' => 'system', 'content' => $system];

$count = 0;
foreach ($input['messages'] as $message) {
    if (!is_array($message)) continue;
    $role = $message['role'] ?? '';
    $text = $message['content'] ?? '';
    if (!in_array($role, ['user', 'assistant'], true) || !is_string($text)) continue;
    $text = trim($text);
    if ($text === '') continue;
    $messages[] = ['role' => $role, 'content' => mb_substr($text, 0, 1200)];
    $count++;
}
if ($count === 0) {
    http_response_code(400);
    echo json_encode(['error' => 'Please send a question first.']);
    exit;
}
if ($count > 10) $messages = array_merge([$messages[0]], array_slice($messages, -10));

$payload = json_encode([
    'model' => $model,
    'messages' => $messages,
    'temperature' => 0.4,
    'max_tokens' => 500
], JSON_UNESCAPED_SLASHES);

$ch = curl_init($apiUrl);
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_CONNECTTIMEOUT => 10,
    CURLOPT_TIMEOUT => 35,
    CURLOPT_HTTPHEADER => [
        'Content-Type: application/json',
        'Authorization: Bearer ' . $apiKey,
        'Accept: application/json'
    ],
    CURLOPT_POSTFIELDS => $payload,
]);
$body = curl_exec($ch);
$status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curlError = curl_error($ch);
curl_close($ch);

if ($body === false || $curlError !== '') {
    error_log('StaxTech AI proxy connection failure: ' . $curlError);
    http_response_code(502);
    echo json_encode(['error' => 'Could not connect to the AI service. Please try again.']);
    exit;
}

$data = json_decode($body, true);
if ($status < 200 || $status >= 300) {
    error_log('StaxTech AI provider returned HTTP ' . $status);
    http_response_code(502);
    echo json_encode(['error' => 'The AI service could not answer right now. Please try again later.']);
    exit;
}

$reply = $data['choices'][0]['message']['content'] ?? null;
if (!is_string($reply) || trim($reply) === '') {
    http_response_code(502);
    echo json_encode(['error' => 'The AI service returned an unexpected response.']);
    exit;
}

echo json_encode(['reply' => trim($reply)], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
