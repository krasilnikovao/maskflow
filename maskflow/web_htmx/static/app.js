document.querySelectorAll("[data-mask-form]").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const target = document.querySelector("#mask-result");
    if (!(target instanceof HTMLElement)) {
      return;
    }

    const response = await fetch(form.action, {
      method: "POST",
      body: new URLSearchParams(new FormData(form)),
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });

    target.innerHTML = await response.text();
  });
});
