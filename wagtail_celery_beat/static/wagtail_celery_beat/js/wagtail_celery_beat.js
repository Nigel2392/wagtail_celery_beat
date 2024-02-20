document.addEventListener('DOMContentLoaded', function() {
    let checkBoxes = document.querySelectorAll('input[name="selected_for_task"]');
    let selectAll = document.querySelector('#wcb_select_all');
    let selectedCount = document.querySelector('#wcb_selected_count');
    let buttons = document.querySelectorAll('.wcb-action-btn');

    function updateButtonEnabled() {
        for (let i = 0; i < buttons.length; i++) {
            if (selectedCount.innerHTML === '0') {
                buttons[i].disabled = true;
            } else {
                buttons[i].disabled = false;
            }
        }
    }

    updateButtonEnabled();

    selectAll.addEventListener('change', function() {
        if (this.checked) {
            for (let i = 0; i < checkBoxes.length; i++) {
                checkBoxes[i].checked = true;
            }
            selectedCount.innerHTML = checkBoxes.length;
        } else {
            for (let i = 0; i < checkBoxes.length; i++) {
                checkBoxes[i].checked = false;
            }
            selectedCount.innerHTML = '0';
        }
        updateButtonEnabled();
    });

    for (let i = 0; i < checkBoxes.length; i++) {
        checkBoxes[i].addEventListener('change', function() {
            let count = 0;
            for (let i = 0; i < checkBoxes.length; i++) {
                if (checkBoxes[i].checked) {
                    count++;
                }
            }
            if (count === checkBoxes.length) {
                selectAll.checked = true;
            } else {
                selectAll.checked = false;
            }
            selectedCount.innerHTML = count;
            updateButtonEnabled();
        });
    }
});
