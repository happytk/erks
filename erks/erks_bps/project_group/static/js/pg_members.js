var roleFormatter = function(value, row, _) {
    var tmpl = '';

    if (row.is_owner) {
        tmpl += gt.gettext('<b><u>그룹소유자</u></b>');
    }
    if (row.is_moderator) {
        tmpl += gt.gettext('<b><u>전사관리자</u></b>');
    }
    if (row.is_termer) {
        tmpl += gt.gettext('<b><u>전사용어관리자</u></b>');
    }
    if (!tmpl.length) {
        return gt.gettext('일반사용자');
    }
    else {
        return tmpl;
    }
};

var roleChangerFormatter = function(value, row, _) {
    "use strict";

    console.log(value, row, _);
    if (value) { //if this is a owner-row, do nothing.
    }
    else {
        var tmpl;
        tmpl = '<a class="btn btn-xs btn-primary btn-role-changer" href="' +
            '/pgu/' + row.id + '/_role_changer' +
            '" data-toggle="modal" data-target="#role-changer-modal">' + gt.gettext('권한설정') + '</a>';
        return tmpl;
    }
};


$('#role-changer-modal').on('hide.bs.modal', function(event) {
    // var button = $(event.relatedTarget);
    // console.log(event);
    // alert(button.closest('tr').data('uniqueid'));
    var $table = $('#project-group-user-table');
    $table.bootstrapTable('refresh');
});


var ProjectGroupShare = function() {

    var $dialog = $('#project-group-share');
    var slug = $dialog.data('project-group-slug');


    var handle_jquery_form_validation_rules = function() {

        jQuery.validator.addMethod("custom_check_multiple_emails_count", function (value, element) {
            if (this.optional(element)) {
                return true;
            }

            var emails = value.split('\n'),
                count = 0,
                val = null
                ;

            for (var i=0, limit=emails.length; i<limit; i++) {
                val = $.trim(emails[i]);
                if (val != "") {
                    count += 1;
                }
            }

            $(element).data('error-cnt', count);

            return count <= 20;
        }, function(params, element) {
            return gt.strargs("한번에 20개의 이메일만 처리가능합니다. 현재 %1개 입력되었습니다.", [$(element).data('error-cnt')]);
        });


        // g_ERROR_EMAILS = "";

        jQuery.validator.addMethod("custom_check_multiple_emails", function (value, element) {
            if (this.optional(element)) {
                return true;
            }

            var emails = value.split('\n'),
                valid = true,
                email_valid = true,
                error_emails = '',
                re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;

            // if (emails.length > 20) {
            //  alert('We can handle only 20 emails per request');
            //  return false;
            // }

            // $.validator.methods.email = function( value, element ) {
            //  return this.optional(element) || re.test(value);
            // }
            for (var i = 0, limit = emails.length; i < limit; i++) {
                value = $.trim(emails[i]);
                if (value == ""){
                    continue;
                }

                email_valid = re.test(value);
                if (!email_valid) {
                    error_emails += '<u>' + value + '</u>; ';
                }
                valid = valid && email_valid; //jQuery.validator.methods.email.call(this, value, element);
            }
            $(element).data('error', error_emails);

            return valid;
        }, function(params, element) {
            return 'Invalid email format. <b>' + $(element).data('error') + '</b>';
        });


    };

    var handle_form_validation = function() {
        $('#form-invitation').validate({
            errorElement: 'p', //default input error message container
            errorClass: 'help-block font-red', // default input error message class
            focusInvalid: false, // do not focus the last invalid input
            rules: {
                emails: {
                    required: true,
                    custom_check_multiple_emails_count: true,
                    custom_check_multiple_emails: true,
                },
            },
        });
    };

    var handle_member_search_form = function() {
        var $search_button = $('#user-search-btn', $dialog);
        var $table = $('#user-search-table', $dialog);
        var $search_input = $('#user-search', $dialog);

        var $bulk_invitation_input = $('#emails', $dialog);
        var $review_button = $('#user-bulk-invitation-review-btn', $dialog);
        var $review_table = $('#user-bulk-invitation-table', $dialog);
        var $review_table_wrapper = $review_table.closest('.form-body');

        $search_button.click(function(e) {
            e.preventDefault();
            $table.bootstrapTable('refresh', {
                //queryParams: userQueryBuilder}); // 동작안함.
                query: {
                    search: $search_input.val()
                }
            });
        });

        $review_button.click(function(e) {
            e.preventDefault();

            var emails = $bulk_invitation_input.val();
            if (!emails.length) {
                return;
            }

            if ($('#form-invitation').validate().valid()) {
                $.ajax({
                    dataType: "json",
                    method: "post",
                    url: Flask.url_for('project_group._invite_review', {slug: slug}),
                    data: {emails: emails},
                    success: function(data) {
                        console.log(data);
                        $review_table.bootstrapTable();
                        $review_table.bootstrapTable('load', data);
                        $review_table_wrapper.show();
                        if ($review_table.bootstrapTable('getSelections')) {
                            $dialog.find('button[type="submit"]').show();
                        }
                        else {
                            $dialog.find('button[type="submit"]').hide();
                        }
                    }
                });
            }
        });
    };

    /*
    프로젝트 초대 action.
    */
    var handle_join_action = function() {
        var $review_table = $('#user-bulk-invitation-table', $dialog);
        var $form = $review_table.closest('form');

        $form.submit(function(e) {
            e.preventDefault();
            var data = null;

            //검토전일 경우 반려
            if ($review_table.is(":visible")) {
                data = $review_table.bootstrapTable('getSelections');
                data = $.map(data, function(row) {
                    return row.user_email;
                });
                // alert(data);
                // return;
            } else {
                App.alert({
                    container: $('.portlet-body:first', $dialog),
                    place: 'prepend', // append or prepent in container
                    type: 'danger', // alert's typexxxx
                    message: gt.gettext('검토 후 초대가능합니다.'),  // alert's message
                    close: true, // make alert closable
                    reset: false, // close all previouse alerts first
                    focus: true, // auto scroll to the alert after shown
                    closeInSeconds: 5, // auto close after defined seconds
                    icon: 'fa fa-check' // put icon class before the message
                });

                return;
            }

            $.ajax({
                dataType: "json",
                method: "post",
                url: Flask.url_for('project_group._invite', {slug: slug}),
                data: {emails: data.join('\n')},
                success: function(data) {
                    App.alert({
                        container: $('#project-group-user-table').closest('.portlet-body'),
                        place: 'prepend', // append or prepent in container
                        type: 'success', // alert's typexxxx
                        message: data.message,  // alert's message
                        close: true, // make alert closable
                        reset: false, // close all previouse alerts first
                        focus: true, // auto scroll to the alert after shown
                        closeInSeconds: 5, // auto close after defined seconds
                        icon: 'fa fa-check' // put icon class before the message
                    });
                    $dialog.modal('hide');
                    $('#project-group-user-table').bootstrapTable('refresh');
                },
                error: function(data) {
                    console.log(data);
                    App.alert({
                        container: $('.portlet-body:first', $dialog),
                        place: 'prepend', // append or prepent in container
                        type: 'danger', // alert's typexxxx
                        message: data.responseJSON.message,  // alert's message
                        close: true, // make alert closable
                        reset: false, // close all previouse alerts first
                        focus: true, // auto scroll to the alert after shown
                        closeInSeconds: 5, // auto close after defined seconds
                        icon: 'fa fa-check' // put icon class before the message
                    });
                }
            });
        });
    };

    var handle_join2_action = function() {
        var $table = $('#user-search-table', $dialog);
        var $submit_btn = $('#user-search-table-selector', $dialog);

        $submit_btn.click(function(e) {
            // e.preventDefault();
            // console.log(e.relatedTarget);
            // var data = $table.bootstrapTable('getData');
            // var emails = $.map(data, function(row) {
            //     if (row.selected || row.selected === undefined) {
            //         return row.user_email;
            //     }
            //     else {
            //         return '';
            //     }
            // });

            var data = $table.bootstrapTable('getSelections');
            var emails = $.map(data, function(row) { return row.user_email; });
            // alert(emails);
            // return;

            $.ajax({
                dataType: "json",
                method: "post",
                url: Flask.url_for('project_group._invite', {slug: slug}),
                data: {emails: emails.join('\n')},
                success: function(data) {
                    App.alert({
                        container: $('#project-group-user-table').closest('.portlet-body'),
                        place: 'prepend', // append or prepent in container
                        type: 'success', // alert's typexxxx
                        message: data.message,  // alert's message
                        close: true, // make alert closable
                        reset: false, // close all previouse alerts first
                        focus: true, // auto scroll to the alert after shown
                        closeInSeconds: 5, // auto close after defined seconds
                        icon: 'fa fa-check' // put icon class before the message
                    });
                    $dialog.modal('hide');
                    $('#project-group-user-table').bootstrapTable('refresh');
                },
                error: function(data) {
                    console.log(data);
                    App.alert({
                        container: $('.portlet-body:first', $dialog),
                        place: 'prepend', // append or prepent in container
                        type: 'danger', // alert's typexxxx
                        message: data.responseJSON.message,  // alert's message
                        close: true, // make alert closable
                        reset: false, // close all previouse alerts first
                        focus: true, // auto scroll to the alert after shown
                        closeInSeconds: 5, // auto close after defined seconds
                        icon: 'fa fa-check' // put icon class before the message
                    });
                }
            });
        });
    };

    return {
        init: function() {
            handle_jquery_form_validation_rules();
            handle_member_search_form();
            handle_form_validation();
            handle_join_action(); // 여러개 넣어서 초대하기
            handle_join2_action(); // 선택해서 초대하기
        }
    };
}();
