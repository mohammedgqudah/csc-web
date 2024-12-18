import bodyParser from 'body-parser'
import express from 'express'

const app = express();
const port = 5002;

app.use(bodyParser.urlencoded({ extended: false }));

let notes = []

app.get('/', (req, res) => {
    res.send(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Notes Form</title>
        </head>
        <body>
            <h1>Submit a Note</h1>
            <form action="/notes" method="POST">
                <label for="title">Title:</label>
                <input type="text" id="title" name="title" required><br><br>
                <label for="content">Content:</label>
                <textarea id="content" name="content" required></textarea><br><br>
                <button type="submit">Submit Note</button>
            </form>
        </body>
        </html>
    `);
});

app.post('/notes', (req, res) => {
	const { title, content } = req.body;

	if (title && content) {
		notes.push({ title, content });
		res.send(`
            <h1>Note Submitted</h1>
            <p>Title: ${title}</p>
            <p>Content: ${content}</p>
            <a href="/">Submit Another Note</a><br>
            <a href="/notes/all">View All Notes</a>
        `);
	} else {
		res.status(400).send('<h1>Error</h1><p>Both title and content are required.</p>');
	}
});


// Endpoint to view all notes
app.get('/notes/all', (req, res) => {
	res.send(`
        <h1>All Notes</h1>
        <ul>
            ${notes.map(note => `<li><strong>${note.title}:</strong> ${note.content}</li>`).join('')}
        </ul>
        <a href="/">Back to form</a>
    `);
});

app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
