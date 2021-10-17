import React from "react";

const FORM_DESTINATION = "http://localhost:5000/add_coffee"

export default function App() {
  const [name, setName] = React.useState("");
  const [coffees, setCoffees] = React.useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    // Add the data to the form
    const form = new FormData();
    form.append("name", name);
    form.append("coffees", coffees);

    const xhr = new XMLHttpRequest()
    // Message on load and error
    xhr.onload = function () {
      if (200 <= xhr.status && xhr.status < 300) {
        // OK
        alert(`${coffees} coffees successfully logged!`)
      } else {
        // Error case
        alert(`${xhr.statusText}\n${xhr.responseText}`);
      }
    };
    xhr.onerror = function () {
      // CORS might trigger this
      alert("Internal error");
    }

    xhr.open("POST", FORM_DESTINATION, true);
    xhr.send(form);
  }

  return (
    <form onSubmit={handleSubmit}>
      <h1>Log Coffee Consumption</h1>

      <label>
        Name:
        <input
          name="name"
          type="text"
          value={name}
          onChange={e => setName(e.target.value)}
          required />
      </label>

      <label>
        Coffees:
        <input
          name="coffees"
          type="number"
          value={coffees}
          onChange={e => setCoffees(e.target.value)}
          required />
      </label>

      <button>Submit</button>
    </form>
  );

}
