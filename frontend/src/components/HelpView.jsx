export default function HelpView({ onBack }) {
  return (
    <section className="panel wide help">
      <div className="toolbar"><button className="secondary" onClick={onBack}>Back</button></div>
      <h2>Voice and text commands</h2>
      <ul>
        <li><code>open VS Code</code>, <code>open chrome</code>, <code>launch notepad</code></li>
        <li><code>make a calculator</code> (creates a folder, writes the code, opens it in VS Code)</li>
        <li><code>make a javascript clock</code> (JavaScript instead of Python)</li>
        <li><code>create a python file called scraper</code></li>
        <li><code>init git</code> and <code>commit</code> (in the current project)</li>
        <li><code>play shape of you</code>, <code>pause</code>, <code>resume</code>, <code>next</code></li>
        <li><code>search for rust borrow checker</code>, <code>open https://example.com</code></li>
        <li><code>press ctrl s in notepad</code> (the window must be focused)</li>
      </ul>
      <h2>Keyboard</h2>
      <ul>
        <li><strong>Ctrl+Space</strong> (hold): push to talk</li>
        <li><strong>Ctrl+Shift+Esc</strong>: abort the running task from anywhere</li>
      </ul>
      <h2>Confirmation policy</h2>
      <p>
        <em>Always Confirm</em> asks before every delete, move, overwrite and program run.
        <em> Confirm Destructive Only</em> lets overwrites through without asking.
        <em> Unattended</em> also skips delete, move and create prompts. Program runs always ask.
      </p>
      <h2>Troubleshooting</h2>
      <ul>
        <li><strong>Cannot reach the backend:</strong> start it with <code>python -m flow</code> in the backend folder.</li>
        <li><strong>Ollama is not running:</strong> start the Ollama app, then retry.</li>
        <li><strong>Model not installed:</strong> run <code>ollama pull &lt;model&gt;</code>, then choose it in Settings.</li>
        <li><strong>Microphone not working:</strong> check the Windows microphone privacy setting and the default device.</li>
      </ul>
    </section>
  );
}
