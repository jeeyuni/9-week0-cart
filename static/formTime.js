function getTimeProp(plus) {
  const now = new Date();
  if (plus !== 0) {
    now.setDate(now.getDate() + plus);
  }
  now.setSeconds(0, 0); // 초, 밀리초 제거
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");

  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

if (document.getElementById("time")) {
  document.getElementById("time").min = getTimeProp(0);
  document.getElementById("time").value = getTimeProp(1);
}

if (document.getElementById("fixtime")) {
  document.getElementById("fixtime").min = getTimeProp(0);
}
