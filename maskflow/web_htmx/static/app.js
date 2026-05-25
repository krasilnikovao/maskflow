document.querySelectorAll("[data-ajax-form]").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const targetSelector = form.getAttribute("data-target");
    const target = targetSelector ? document.querySelector(targetSelector) : null;
    if (!(target instanceof HTMLElement)) {
      return;
    }

    const formData = new FormData(form);
    const isMultipart = form.enctype === "multipart/form-data";
    const response = await fetch(form.action, {
      method: "POST",
      body: isMultipart ? formData : new URLSearchParams(formData),
    });

    target.innerHTML = await response.text();
  });
});
