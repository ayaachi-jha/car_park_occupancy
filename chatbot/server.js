
const express = require('express');
const { OpenAI } = require('openai');
const app = express();
const port = 3000;

app.use(express.static('public'));
app.use(express.json());

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

app.post('/api/chat', async (req, res) => {
  try {
    const { message } = req.body;
    const completion = await openai.chat.completions.create({
      messages: [{ role: 'user', content: message }],
      model: 'gpt-3.5-turbo',
    });

    res.json({ reply: completion.choices[0].message.content });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Error processing your request' });
  }
});

app.listen(port, () => {
  console.log(`Server listening at http://localhost:${port}`);
});
