document.addEventListener(
    "DOMContentLoaded",
    function(){

        const avatarBtn =
        document.getElementById(
            "avatarBtn"
        );

        const dropdownMenu =
        document.getElementById(
            "dropdownMenu"
        );

        if(
            !avatarBtn ||
            !dropdownMenu
        ){
            return;
        }

        avatarBtn.addEventListener(
            "click",
            function(e){

                e.stopPropagation();

                dropdownMenu.classList.toggle(
                    "show"
                );
            }
        );

        document.addEventListener(
            "click",
            function(e){

                if(
                    !dropdownMenu.contains(
                        e.target
                    )
                    &&
                    !avatarBtn.contains(
                        e.target
                    )
                ){

                    dropdownMenu.classList.remove(
                        "show"
                    );
                }
            }
        );

    }
);