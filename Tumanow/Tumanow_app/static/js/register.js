function profile_pic_handler(){
    const uploadIcon = document.getElementById("uploadIcon");
    const profileInput = document.getElementById("profileInput");

    uploadIcon.addEventListener("click", function () {
        profileInput.click();
    });

    profileInput.addEventListener("change", function () {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();

            reader.onload = function (e) {
                const img = document.createElement("img");
                img.src = e.target.result;
                img.style.width = "80px";
                img.style.height = "80px";
                img.style.objectFit = "cover";
                img.style.borderRadius = "50%"; // makes it round
                img.style.cursor = "pointer";

                uploadIcon.replaceWith(img); // replaces icon with image

                // If you still want to re-open file input on click:
                img.addEventListener("click", function () {
                    profileInput.click();
                });
            };

            reader.readAsDataURL(file);
        }
    });
}

document.addEventListener('DOMContentLoaded', function(){
    profile_pic_handler();
});