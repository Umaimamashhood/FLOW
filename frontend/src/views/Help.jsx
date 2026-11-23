export default function Help() {
  return (
    <div className="page">
      <header className="page-head">
        <div>
          <p className="eyebrow">Getting started</p>
          <h1>Help</h1>
        </div>
      </header>

      <div className="grid-2">
        <section className="card">
          <h3>Things to ask</h3>
          <ul className="plain">
            <li><code>open gmail</code> or <code>open classroom</code></li>
            <li><code>play shape of you</code>, then <code>pause</code> or <code>next</code></li>
            <li><code>make a calculator and run it</code></li>
            <li><code>create a python file called scraper</code></li>
            <li><code>increase the volume</code></li>
            <li><code>what is 12 times 7</code></li>
          </ul>
        </section>

        <section className="card">
          <h3>Shortcuts</h3>
          <ul className="plain">
            <li><kbd>Ctrl</kbd> + <kbd>Space</kbd> hold to talk</li>
            <li><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>Esc</kbd> stop the running task</li>
          </ul>
          <h3 className="mt">Approvals</h3>
          <p className="muted">FLOW asks before it deletes, moves, overwrites, installs packages, runs a program, or runs a command.</p>
        </section>

        <section className="card wide-card">
          <h3>If something is wrong</h3>
          <ul className="plain">
            <li><strong>Backend offline:</strong> run <code>python main.py</code> in the backend folder.</li>
            <li><strong>No model:</strong> start Ollama and run <code>ollama pull qwen2.5-coder:7b</code>.</li>
            <li><strong>Voice not working:</strong> run <code>python -m pip install -r requirements.txt</code> in the backend environment, and check the microphone permission.</li>
          </ul>
        </section>
      </div>
    </div>
  );
}
