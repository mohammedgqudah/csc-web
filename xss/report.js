import puppeteer from 'puppeteer'
import bodyParser from 'body-parser'
import express from 'express'

async function visit(url) {
	const browser = await puppeteer.launch({
		//executablePath: '/usr/bin/google-chrome-stable'
		headless: true,
		args: [
			'--disable-dev-shm-usage',
			'--no-sandbox',
			'--disable-setuid-sandbox',
			'--disable-gpu',
			'--no-gpu',
			'--disable-default-apps',
			'--disable-translate',
			'--disable-device-discovery-notifications',
			'--disable-software-rasterizer',
		]
	});
	const page = await browser.newPage();

	browser.setCookie({
		'name': 'token',
		'value': process.env.FLAG || 'this_is_a_secret',
		'domain': 'localhost:5002'

	})

	let response = await page.goto(url);

	await page.waitForNetworkIdle();

	// when doing CTF challenges, adding this line will help with debugging
	console.log(await response.text())

	console.log('Visited URL: "%s".', url);

	await browser.close();
}


const app = express();
const port = 5000;

app.use(bodyParser.urlencoded({ extended: false }));

app.get('/report', (req, res) => {
	res.send(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Report to admins</title>
        </head>
        <body>
            <h1>Submit a URL to report and one of the admins will visit is it in a moment</h1>
            <form action="/report" method="POST">
                <label for="title">URL:</label>
                <input type="text" id="url" name="url" required><br><br>
                <button type="submit">Report</button>
            </form>
        </body>
        </html>
    `);
});

app.post('/report', async (req, res) => {
	const { url } = req.body;

	await visit(url);

	res.send(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>URL Reported</title>
        </head>
        <body>
            <h1>URL reported successfully</h1>
        </body>
        </html>
    `);
});

app.listen(port, () => {
	console.log(`Report bot is running on http://localhost:${port}`);
});
