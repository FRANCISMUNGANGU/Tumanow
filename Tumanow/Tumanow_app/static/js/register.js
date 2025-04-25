function profile_click(){
    let profile_icon = document.getElementById('profile_upload');
    let profile_input = document.getElementById('profile_input');
    profile_icon.addEventListener('click', function(){
        profile_input.click()
    });

    profile_input.addEventListener('change', function(){
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
                img.style.alignSelf = "center";

                profile_icon.replaceWith(img); // replaces icon with image

                // If you still want to re-open file input on click:
                img.addEventListener("click", function () {
                    profileInput.click();
                });
            };

            reader.readAsDataURL(file);
        }
    })
}

document.addEventListener('DOMContentLoaded', function(){
    profile_click()
})