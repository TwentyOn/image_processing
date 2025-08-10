const btn = document.querySelector(".btn");
const input = document.querySelector(".pic");
const imgElem = document.getElementById("processed-image")
const linkElem = document.getElementById("download-link")

btn.addEventListener("click", async function (e) {
  e.preventDefault();
  const pic = input.files?.[0];
  if (!pic) {
    alert("Выберите файл");
    return;
  } /* Если будет мешать, удали кусок if */

  const formData = new FormData();
  formData.append("format", "png");
  formData.append("quality", 75);
  formData.append("resolution", "true");
  formData.append("proportion", "true");
  formData.append("toggleSwitch", "true");
  formData.append("high", "1200");
  formData.append("width", "600");
  formData.append("file", pic);

  const response = await fetch("http://127.0.0.1:8000/api/image_processing/", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    console.error(await response.text());
    alert("Ошибка загрузки/обработки");
    return;
  } /* Если будет мешать, удали кусок if */

  const blob = await response.blob(); // получаем бинарные данные

  // Делаем временный URL для картинки в браузере
  const objectUrl = URL.createObjectURL(blob);
  // Вставляем в <img>
  imgElem.src = objectUrl;

  // Делаем ссылку для скачивания
  linkElem.href = objectUrl;
});