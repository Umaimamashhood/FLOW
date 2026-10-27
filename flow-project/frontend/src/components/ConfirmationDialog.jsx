import { useState } from "react";
import Modal from "./Modal";

// Shows the proposed action (or the program source) and lets the user pick a search result when offered.
export default function ConfirmationDialog({ awaiting, onDecide }) {
  const [choice, setChoice] = useState(0);
  const options = awaiting.options || [];
  return (
    <Modal
      title="Confirm action"
      confirmLabel={options.length ? "Play selected" : "Confirm"}
      onCancel={() => onDecide(false, null)}
      onConfirm={() => onDecide(true, options.length ? choice : null)}
    >
      <pre className="message">{awaiting.message}</pre>
      {options.length > 0 && (
        <fieldset className="choices">
          <legend>Choose a result</legend>
          {options.map((title, i) => (
            <label key={i}>
              <input type="radio" name="choice" checked={choice === i} onChange={() => setChoice(i)} />
              {title}
            </label>
          ))}
        </fieldset>
      )}
    </Modal>
  );
}
