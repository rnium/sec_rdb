const showError = msg => {
    $("#signupAlert").removeClass('alert-info');
    $("#signupAlert").addClass('alert-warning');
    $("#signupAlert").text(msg);
    $("#signupAlert").show();
}

const showInfo = msg => {
    $("#signupAlert").removeClass('alert-warning');
    $("#signupAlert").addClass('alert-info');
    $("#signupAlert").text(msg);
    $("#signupAlert").show();
}

function getFormData() {
    data = {};
    let first_name = $("#firstNameInput").val().trim();
    let last_name = $("#lastNameInput").val().trim();
    let password = $("#passwordInput").val().trim();
    let password_retype = $("#passwordInputRepeat").val().trim();
    if (first_name.length == 0) {
        showError("Please Enter First Name")
        return false;
    }
    if (password.length < 8) {
        showError("Password must be at least 8 characters long")
        return false;
    }
    if (password != password_retype) {
        showError("Passwords does not matches")
        return false;
    } else {
        $("#signupAlert").hide(); 
    }
    data.first_name = first_name;
    data.password = password;
    if (last_name.length > 0) {
        data.last_name = last_name;
    }
    return data;
}

function performSignnup() {
    payload = getFormData();
    if (payload) {
        $.ajax({
            type: "post",
            url: create_admin_account_api,
            dataType: "json",
            contentType: "application/json",
            beforeSend: function(xhr){
                $("#create-ac-btn").attr("disabled", true);
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response) {
                showInfo(response['status']);
            },
            error: function(xhr, status, error) {
                $("#create-ac-btn").attr("disabled", false);
                showError(xhr.responseJSON.details);
            },
        });
    }
}

$(document).ready(function () {
    $("#create-ac-btn").on('click', performSignnup);
});