export function renderErrorPage(): string {
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Application Error</title>
    <style>
      body {
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        font-family: system-ui, sans-serif;
        background: #f8fafc;
        color: #0f172a;
      }

      main {
        max-width: 560px;
        padding: 32px;
        text-align: center;
      }

      h1 {
        margin-bottom: 12px;
      }

      p {
        color: #475569;
      }
    </style>
  </head>
  <body>
    <main>
      <h1>Something went wrong</h1>
      <p>
        The application encountered an unexpected server error.
        Please try again.
      </p>
    </main>
  </body>
</html>`;
}