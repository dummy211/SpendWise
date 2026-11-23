const howItWorksButton = document.querySelector("#show-how-it-works");
const videoModal = document.querySelector("#how-it-works-modal");

if (howItWorksButton instanceof HTMLButtonElement && videoModal instanceof HTMLDialogElement) {
    const videoFrame = videoModal.querySelector(".video-modal-frame");
    const closeButton = videoModal.querySelector(".video-modal-close");

    howItWorksButton.addEventListener("click", () => {
        const iframe = document.createElement("iframe");
        iframe.src = "https://www.youtube-nocookie.com/embed/MP4F0ZcW_G0?autoplay=1&rel=0";
        iframe.title = "Spendly: See how it works";
        iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
        iframe.allowFullscreen = true;

        videoModal.showModal();
        videoFrame.append(iframe);
    });

    closeButton.addEventListener("click", () => videoModal.close());
    videoModal.addEventListener("click", (event) => {
        if (event.target === videoModal) {
            videoModal.close();
        }
    });
    videoModal.addEventListener("close", () => videoFrame.replaceChildren());
}
