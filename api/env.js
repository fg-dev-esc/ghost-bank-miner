const PUBLIC_ENV_KEYS = [
  'GROQ_API_KEY',
  'OPENROUTER_API_KEY',
  'GOOGLE_API_KEY',
  'MISTRAL_API_KEY',
  'SAMBANOVA_API_KEY',
  'COHERE_API_KEY',
  'CEREBRAS_API_KEY',
];

module.exports = function handler(req, res) {
  // Habilitar CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const env = {};
  for (const key of PUBLIC_ENV_KEYS) {
    env[key] = process.env[key] || '';
  }

  return res.status(200).json(env);
};
