async function uploadFile() {
  const fileInput = document.getElementById("fileInput");
  const status = document.getElementById("status");

  if (!fileInput.files.length) {
    status.innerText = "Please select a file";
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  status.innerText = "Uploading...";

  const response = await fetch("http://localhost:8000/upload", {
    method: "POST",
    body: formData
  });

  if (response.ok) {
    window.location.href = "dashboard.html";
  } else {
    status.innerText = "Upload failed";
  }
}
