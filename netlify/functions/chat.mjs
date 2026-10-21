export default async (request) => {
  if (request.method !== "POST") {
    return json({ error: "Use POST for chat requests." }, 405);
  }

  const apiKey = process.env.AI_API_KEY || "";
  const apiUrl = process.env.AI_API_URL || "https://codecraftapi.com/v1/chat/completions";
  const model = process.env.AI_MODEL || "claude-opus-4.8";

  if (!apiKey) {
    return json({ error: "The AI assistant is not configured yet. Please contact the site administrator." }, 503);
  }

  let input;
  try {
    input = await request.json();
  } catch {
    return json({ error: "Invalid request payload." }, 400);
  }

  if (!input || !Array.isArray(input.messages)) {
    return json({ error: "Invalid request payload." }, 400);
  }

  const system = "You are the helpful StaxTech website assistant. Answer clearly and politely. You may help with StaxTech services, internship applications, website navigation, and general questions. For official program details you are unsure about, direct users to https://staxtech.in or info@staxtech.in. Never claim to have completed an action you cannot perform. Do not ask users for passwords, OTPs, payment card details, or secret information. Keep responses concise.";

  const messages = [{ role: "system", content: system }];
  let count = 0;

  for (const message of input.messages) {
    if (!message || typeof message !== "object") continue;
    const role = message.role;
    const text = message.content;
    if (!["user", "assistant"].includes(role) || typeof text !== "string") continue;
    const trimmed = text.trim();
    if (!trimmed) continue;
    messages.push({ role, content: trimmed.slice(0, 1200) });
    count++;
  }

  if (count === 0) {
    return json({ error: "Please send a question first." }, 400);
  }

  if (count > 10) {
    messages.splice(1, messages.length - 11);
  }

  let providerResponse;
  try {
    providerResponse = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${apiKey}`,
        "Accept": "application/json"
      },
      body: JSON.stringify({
        model,
        messages,
        temperature: 0.4,
        max_tokens: 500
      })
    });
  } catch (error) {
    console.error("StaxTech AI provider connection failure:", error);
    return json({ error: "Could not connect to the AI service. Please try again." }, 502);
  }

  if (!providerResponse.ok) {
    console.error("StaxTech AI provider returned HTTP", providerResponse.status);
    return json({ error: "The AI service could not answer right now. Please try again later." }, 502);
  }

  let data;
  try {
    data = await providerResponse.json();
  } catch {
    return json({ error: "The AI service returned an unexpected response." }, 502);
  }

  const reply = data?.choices?.[0]?.message?.content;
  if (typeof reply !== "string" || !reply.trim()) {
    return json({ error: "The AI service returned an unexpected response." }, 502);
  }

  return json({ reply: reply.trim() }, 200);
};

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff"
    }
  });
}
