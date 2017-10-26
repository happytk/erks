var Login = function () {

    var handleLogin = function() {
        $('.alert span a').click(function(){

            var form = $(document.createElement('form'));
            $(form).attr('action', Flask.url_for('login.resend_verifying_mail'));
            $(form).attr("method", "POST");

            var input = $("<input>").attr("type", "hidden").attr("name", "email").val($('.login-form #email').val());
            $(form).append($(input));
            $(form).submit();

        });

        $('.login-form').validate({
                errorElement: 'span', //default input error message container
                errorClass: 'help-block', // default input error message class
                focusInvalid: false, // do not focus the last invalid input
                rules: {
                    email: {
                        required: true
                    },
                    password: {
                        required: true
                    },
                    remember: {
                        required: false
                    }
                },

                messages: {
                    email: {
                        required: _("이메일을 입력해 주세요.")
                    },
                    password: {
                        required: _("비밀번호를 입력해 주세요.")
                    }
                },

                invalidHandler: function (event, validator) { //display error alert on form submit
                    $('.alert-danger', $('.login-form')).show();
                },

                highlight: function (element) { // hightlight error inputs
                    $(element)
                        .closest('.form-group').addClass('has-error'); // set error class to the control group
                },

                success: function (label) {
                    label.closest('.form-group').removeClass('has-error');
                    label.remove();
                },

                errorPlacement: function (error, element) {
                    error.insertAfter(element.closest('.input-icon'));
                },

                submitHandler: function (form) {
                    form.submit();
                }
            });

            $('.login-form input').keypress(function (e) {
                if (e.which == 13) {
                    if ($('.login-form').validate().form()) {
                        $('.login-form').submit();
                    }
                    return false;
                }
            });
    }

    var handleForgetPassword = function () {
        $('.forget-form').validate({
                errorElement: 'span', //default input error message container
                errorClass: 'help-block', // default input error message class
                focusInvalid: false, // do not focus the last invalid input
                ignore: "",
                rules: {
                    email: {
                        required: true,
                        email: true
                    }
                },

                messages: {
                    email: {
                        required: _("이메일을 입력해 주세요.")
                    }
                },

                invalidHandler: function (event, validator) { //display error alert on form submit

                },

                highlight: function (element) { // hightlight error inputs
                    $(element)
                        .closest('.form-group').addClass('has-error'); // set error class to the control group
                },

                success: function (label) {
                    label.closest('.form-group').removeClass('has-error');
                    label.remove();
                },

                errorPlacement: function (error, element) {
                    error.insertAfter(element.closest('.input-icon'));
                },

                submitHandler: function (form) {
                    form.submit();
                }
            });

            $('.forget-form input').keypress(function (e) {
                if (e.which == 13) {
                    if ($('.forget-form').validate().form()) {
                        $('.forget-form').submit();
                    }
                    return false;
                }
            });

            // jQuery('#forget-password').click(function () {
            //     jQuery('.login-form').hide();
            //     jQuery('.forget-form').show();
            // });

            // jQuery('#back-btn').click(function () {
            //     jQuery('.login-form').show();
            //     jQuery('.forget-form').hide();
            // });

    }

    var handleRegister = function () {

        function format(state) {
            if (!state.id) return state.text; // optgroup
            return "<img class='flag' src='../../assets/global/img/flags/" + state.id.toLowerCase() + ".png'/>&nbsp;&nbsp;" + state.text;
        }


        // $("#select2_sample4").select2({
        //     placeholder: '<i class="fa fa-map-marker"></i>&nbsp;Select a Country',
        //     allowClear: true,
        //     formatResult: format,
        //     formatSelection: format,
        //     escapeMarkup: function (m) {
        //         return m;
        //     }
        // });

        // $('#select2_sample4').change(function () {
        //     $('.register-form').validate().element($(this)); //revalidate the chosen dropdown value and show error or success message for the input
        // });

        $('.register-form').validate({
            errorElement: 'span', //default input error message container
            errorClass: 'help-block', // default input error message class
            focusInvalid: false, // do not focus the last invalid input
            ignore: "",
            rules: {
                // fullname: {
                //     required: true
                // },
                email: {
                    required: true,
                    email: true
                },
                // address: {
                //     required: true
                // },
                // city: {
                //     required: true
                // },
                // country: {
                //     required: true
                // },

                username: {
                    required: true
                },
                password: {
                    required: true
                },
                password_confirm: {
                    required: true,
                    equalTo: "#register_password"
                },

                chk_term_of_service: {
                    required: true
                },
                chk_privacy_policy: {
                    required: true
                },
                chk_privacy_policy_agree: {
                    required: true
                }
            },
            messages: { // custom messages for radio buttons and checkboxes
                email: {
                        required: _("이메일을 입력해 주세요.")
                    },
                    password: {
                        required: _("비밀번호를 입력해 주세요.")
                    },
                    password_confirm: {
                        required: _("비밀번호를 다시 한번 입력해 주세요.")
                    },
                chk_term_of_service: {
                    required: _("서비스 이용 약관 및 개인정보 정책을 동의해주세요.")
                },
                chk_privacy_policy: {
                    required: _("개인정보 처리방침을 동의해주세요.")
                },
                chk_privacy_policy_agree: {
                    required: _("개인정보의 수집∙이용 동의서에 동의해주세요.")
                }
            },

            invalidHandler: function (event, validator) { //display error alert on form submit
                },

            highlight: function (element) { // hightlight error inputs
                    $(element)
                        .closest('.form-group').addClass('has-error'); // set error class to the control group
            },

            success: function (label) {
                label.closest('.form-group').removeClass('has-error');
                label.remove();
            },

            errorPlacement: function (error, element) {
                if (element.attr("name") == "chk_term_of_service") { // insert checkbox errors after the container
                    error.insertAfter($('#register_term_of_service_error'));

                } else if (element.attr("name") == "chk_privacy_policy") {
                    error.insertAfter($('#register_privacy_policy_error'));

                } else if (element.attr("name") == "chk_privacy_policy_agree") {
                    error.insertAfter($('#register_privacy_policy_agree_error'));
                    
                } else if (element.closest('.input-icon').size() === 1) {
                    error.insertAfter(element.closest('.input-icon'));
                } else {
                    error.insertAfter(element);
                }
            },

            submitHandler: function (form) {
                form.submit();
            }
        });

        $('.register-form input').keypress(function (e) {
            if (e.which == 13) {
                if ($('.register-form').validate().form()) {
                    $('.register-form').submit();
                }
                return false;
            }
        });

        // jQuery('#register-btn').click(function () {
        //     jQuery('.login-form').hide();
        //     jQuery('.register-form').show();
        // });

        // jQuery('#register-back-btn').click(function () {
        //     jQuery('.login-form').show();
        //     jQuery('.register-form').hide();
        // });

        $('#btn_term_of_service').click(function(){
            bootbox.dialog({
                title: _("NEXCORE ER-C 서비스 이용 약관"),
                message: $('#contents_term_of_service').html(),
                buttons: {
                  success: {
                    label: "닫기",
                    className: "green",
                    callback: function() {
                      return;
                    }
                  },
                }
            });
        });

        $('#btn_privacy_policy').click(function(){
            bootbox.dialog({
                title: _("NEXCORE ER-C 개인정보 처리방침"),
                message: $('#contents_privacy_policy').html(),
                buttons: {
                  success: {
                    label: "닫기",
                    className: "green",
                    callback: function() {
                      return;
                    }
                  },
                }
            });
        });

        $('#btn_privacy_policy_agree').click(function(){
            bootbox.dialog({
                title: _("NEXCORE ER-C 개인정보 수집∙이용 동의서"),
                message: $('#contents_privacy_policy_agree').html(),
                buttons: {
                  success: {
                    label: _("닫기"),
                    className: "green",
                    callback: function() {
                      return;
                    }
                  },
                }
            });
        });

    }

    return {
        //main function to initiate the module
        init: function () {
            handleLogin();
            handleForgetPassword();
            handleRegister();
        }
    };
}();