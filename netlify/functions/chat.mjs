const CODECRAFT_URL = 'https://codecraftapi.com/v1/chat/completions';

const SITE_ROUTES = ['/', '/about', '/services', '/apply', '/offer', '/instructions', '/project-submission', '/verifycert-new', '/server', '/terms', '/articles', '/tools'];

function json(status, data) {
  return { statusCode: status, headers: {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Methods': 'POST, OPTIONS'
  }, body: JSON.stringify(data) };
}

function lastUserText(messages = []) {
  const m = [...messages].reverse().find(x => x?.role === 'user');
  return typeof m?.content === 'string' ? m.content : '';
}

export default async (request) => {
  if (request.method === 'OPTIONS') return json(204, {});
  if (request.method !== 'POST') return json(405, { error: 'Method not allowed' });

  const apiKey = process.env.CODECRAFT_API_KEY;
  if (!apiKey) return json(500, { error: 'CODECRAFT_API_KEY is not configured in Netlify environment variables.' });

  try {
    const input = await request.json();
    const messages = Array.isArray(input.messages) ? input.messages : [];
    const userText = lastUserText(messages);
    const lower = userText.toLowerCase();

    let toolContext = '';
    if (/offer|offer letter|joining|internship letter/.test(lower)) {
      toolContext += '\nOffer Letter Finder: ask for the registered email or phone number and direct the user to https://staxtech.in/offer for the live search.\n';
    }
    if (/certificate|certificat|verify|verification/.test(lower)) {
      toolContext += '\nCertificate Verification: ask for the Certificate ID and direct the user to https://staxtech.in/verifycert-new.html for live verification and download.\n';
    }

    const system = `You are the official StaxTech website assistant. Use StaxTech website information first. Be concise and accurate. Never invent internship, offer-letter, certificate, fee, eligibility, contact, or policy details. Help users navigate the website, find offer letters, verify certificates, understand internship instructions, submit projects, and explain StaxTech services. Important pages: ${SITE_ROUTES.map(x => 'https://staxtech.in' + x).join(', ')}. Offer Letter Finder: https://staxtech.in/offer. Certificate Verification: https://staxtech.in/verifycert-new.html. Instructions: https://staxtech.in/instructions. Project Submission: https://staxtech.in/project-submission. ${toolContext}`;

    const upstream = await fetch(CODECRAFT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiKey}` },
      body: JSON.stringify({
        model: input.model || 'claude-opus-4.8',
        messages: [{ role: 'system', content: system }, ...messages.filter(m => m?.role !== 'system').slice(-12)],
        temperature: 0.4,
        max_tokens: 4096
      }),
      signal: AbortSignal.timeout(60000)
    });

    const text = await upstream.text();
    let data; try { data = JSON.parse(text); } catch { data = { error: text }; }
    return json(upstream.status, data);
  } catch (error) {
    return json(500, { error: error?.message || 'Chat proxy error' });
  }
};
