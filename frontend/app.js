// =====================================================================
// Frontend logic (plain JavaScript, no framework).
// It talks to the backend with fetch():
//   GET    /documents        -> show the list
//   POST   /documents        -> upload a file (FormData)
//   DELETE /documents/{id}   -> delete a file
//   POST   /ask              -> ask a question about the checked documents
// Everything the user or the server writes is shown with textContent
// (never innerHTML), so it can never run as code in the page.
// =====================================================================

const fileInput = document.getElementById("fileInput");
const dropZone = document.getElementById("dropZone");
const uploadStatus = document.getElementById("uploadStatus");
const documentList = document.getElementById("documentList");
const emptyMessage = document.getElementById("emptyMessage");
const questionBox = document.getElementById("question");
const askButton = document.getElementById("askButton");
const answerBox = document.getElementById("answerBox");
const answerDiv = document.getElementById("answer");
const answerInfo = document.getElementById("answerInfo");
const sourcesDiv = document.getElementById("sources");


// ---------- helpers ----------

// Turn an error response from FastAPI into a readable message
async function readError(response) {
  try {
    const data = await response.json();
    return typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
  } catch {
    return "Error " + response.status;
  }
}

function addStatusLine(text, cssClass) {
  const li = document.createElement("li");
  li.textContent = text;
  if (cssClass) li.className = cssClass;
  uploadStatus.appendChild(li);
  return li;
}


// ---------- 1. document list ----------

async function loadDocuments() {
  const response = await fetch("/documents");
  const documents = await response.json();

  documentList.innerHTML = "";   // empty the list (our own HTML, safe)
  emptyMessage.classList.toggle("hidden", documents.length > 0);

  for (const doc of documents) {
    const li = document.createElement("li");

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = true;
    checkbox.value = doc.id;
    checkbox.className = "doc-checkbox";

    const name = document.createElement("span");
    name.className = "name";
    name.textContent = doc.filename;

    const info = document.createElement("span");
    info.className = "info";
    info.textContent = `${doc.pages} page(s) · ${doc.chunks} chunk(s)`;

    const deleteButton = document.createElement("button");
    deleteButton.className = "delete-button";
    deleteButton.textContent = "🗑";
    deleteButton.title = "Delete";
    deleteButton.onclick = () => deleteDocument(doc.id, doc.filename);

    li.append(checkbox, name, info, deleteButton);
    documentList.appendChild(li);
  }
}

async function deleteDocument(id, filename) {
  if (!confirm(`Delete "${filename}"?`)) return;
  const response = await fetch("/documents/" + id, { method: "DELETE" });
  if (!response.ok) {
    alert(await readError(response));
  }
  loadDocuments();
}

function getCheckedDocumentIds() {
  const boxes = document.querySelectorAll(".doc-checkbox:checked");
  return Array.from(boxes).map(box => box.value);
}


// ---------- 2. upload ----------

async function uploadFiles(files) {
  // Copy the list first: the file input is emptied right after, while we are still uploading
  const fileArray = Array.from(files);

  // One file at a time, so each one gets its own status line
  for (const file of fileArray) {
    const line = addStatusLine(`⏳ Uploading and indexing ${file.name}...`);

    const formData = new FormData();          // FormData = how browsers send files
    formData.append("file", file);            // "file" must match the name in main.py

    try {
      const response = await fetch("/documents", { method: "POST", body: formData });
      if (response.ok) {
        const doc = await response.json();
        line.textContent = `✅ ${doc.filename}: ${doc.pages} page(s), ${doc.chunks} chunk(s)`;
        line.className = "ok";
      } else {
        line.textContent = `❌ ${file.name}: ${await readError(response)}`;
        line.className = "error";
      }
    } catch {
      line.textContent = `❌ ${file.name}: could not reach the server`;
      line.className = "error";
    }
    loadDocuments();
  }
}

fileInput.addEventListener("change", () => {
  uploadFiles(fileInput.files);
  fileInput.value = "";   // allow choosing the same file again later
});

// Drag and drop
dropZone.addEventListener("dragover", event => {
  event.preventDefault();                     // needed, otherwise the browser opens the file
  dropZone.classList.add("dragging");
});
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragging"));
dropZone.addEventListener("drop", event => {
  event.preventDefault();
  dropZone.classList.remove("dragging");
  uploadFiles(event.dataTransfer.files);
});


// ---------- 3. ask ----------

async function askQuestion() {
  const question = questionBox.value.trim();
  if (question.length < 3) {
    alert("Please write a longer question.");
    return;
  }
  const documentIds = getCheckedDocumentIds();
  if (documentIds.length === 0) {
    alert("Upload a document, or check at least one.");
    return;
  }

  askButton.disabled = true;
  askButton.textContent = "Thinking...";
  answerBox.classList.remove("hidden");
  answerDiv.className = "answer";
  answerDiv.textContent = "...";
  answerInfo.textContent = "";
  sourcesDiv.innerHTML = "";

  try {
    const response = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question, document_ids: documentIds }),
    });

    if (!response.ok) {
      answerDiv.className = "answer error";
      answerDiv.textContent = "Error: " + await readError(response);
      return;
    }

    const data = await response.json();
    answerDiv.textContent = data.answer;
    answerInfo.textContent = `Answered by ${data.model} in ${data.seconds} s`;

    for (const s of data.sources) {
      const div = document.createElement("div");
      div.className = "source";

      const title = document.createElement("b");
      title.textContent = `[${s.number}] ${s.source}, page ${s.page}`;
      const score = document.createTextNode(`  (similarity ${s.score})`);
      const preview = document.createElement("div");
      preview.className = "preview";
      preview.textContent = s.preview + "...";

      div.append(title, score, preview);
      sourcesDiv.appendChild(div);
    }
  } catch {
    answerDiv.className = "answer error";
    answerDiv.textContent = "Could not reach the server. Is it running?";
  } finally {
    askButton.disabled = false;
    askButton.textContent = "Ask";
  }
}

askButton.addEventListener("click", askQuestion);
questionBox.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) {   // Enter = ask, Shift+Enter = new line
    event.preventDefault();
    askQuestion();
  }
});


// ---------- start ----------
loadDocuments();