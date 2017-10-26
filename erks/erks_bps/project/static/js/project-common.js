var lastSelectedNode = null;

function showSjaTree(requestedPrjId) {

    var prjId=requestedPrjId;
    $.jstree._themes = "/static/css/jstreeThemes/";
    $.support.cors = true;


    //주제영역 Tree Loading
    $.ajax({
        url: Flask.url_for('erc.get_minimal_subj_tree', {project_id: prjId}),
        type: 'POST',
        contentType: "application/json;charset=utf-8",
        dataType: 'json',
        data: JSON.stringify({"prjId":prjId}),
        success: function(sjaJson){
            // xx = sjaJson;
            if (sjaJson && sjaJson.tree && sjaJson.tree.length) {
                $('#sja_pjt')
                    .jstree({
                        'plugins':["types"],
                        'core' : {
                            "check_callback" : true,
                            'data' : sjaJson.tree
                        },
                        'types' : {
                            "model" : { "icon" : "/erc/static/img/dataModel.png"},
                            "domains" : { "icon" : "/erc/static/img/domains.png"},
                            "entities" : { "icon" : "/erc/static/img/Entities.png"},
                            "subjects" : { "icon" : "/erc/static/img/subjectArea.png"},
                            "subject" : { "icon" : "/erc/static/img/erd_page.png"}, // ERD ID가 매핑된 대상
                            "domain" : { "icon" : "/erc/static/img/domain.png"},
                            "entity" : { "icon" : "/erc/static/img/Entity.png"},
                            "default" : { "icon" : "/erc/static/img/erd_folder.png"} // ERD ID가 없는 대상
                        }
                    })
                    .on("click.jstree", function (event) {
                        var ref = $('#sja_pjt').jstree(true),
                            sel = ref.get_selected();
                        var selnode = ref.get_node(sel[0]);

                        if (selnode.a_attr && selnode.a_attr.objectId !== undefined && selnode.type == 'subject')
                        {
                            var url = '/erc/ercapp/'+prjId;
                            var form = $('<form action="' + url + '" method="post">' +
                                      '<input type="text" name="subjId" value="' + selnode.a_attr.objectId + '" />' +
                                      '</form>');
                            $('body').append(form);
                            form.submit();
                        }
                        if (selnode.type == 'model' || selnode.type == 'subjects')
                        {
                            $('#sja_pjt').jstree("toggle_node",selnode);
                        }
                        if (selnode.type == 'model'){
                            $("#sja_pjt").jstree("open_node", '#'+selnode.children[0]);
                        }
                    });

                    $('#sja_pjt').jstree('close_all');
            }
            else {
                $('#sja_pjt').html(_('등록된 주제영역이 없습니다.'));
            }
        },
        statusCode: {
            404: function() {
                alert("page not found");
                }
        },
        complete: function(){

        }
    });
}

var ProjectShare = function() {

    var $dialog = $('#share_project');
    // var project_id = $dialog.data('project-id');

    var handle_jquery_form_validation_rules = function(project_id) {

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

    var handle_form_validation = function(project_id) {
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

    var handle_member_search_form = function(project_id) {
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
                    url: Flask.url_for('project._invite_review', {project_id: project_id}),
                    data: {emails: emails},
                    success: function(data) {
                        $review_table.bootstrapTable();
                        $review_table.bootstrapTable('load', data);
                        $review_table_wrapper.show();
                        console.log($review_table.bootstrapTable('getSelections'));
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
    var handle_join_action = function(project_id) {
        var $form = $('form', $dialog);
        var $review_table = $('#user-bulk-invitation-table', $dialog);

        $form.submit(function(e) {
            e.preventDefault();
            var data = null;

            //검토전일 경우 반려
            if ($review_table.is(":visible")) {
                data = $review_table.bootstrapTable('getSelections');
                data = $.map(data, function(row) {
                    return row.user_email;
                });
            } else {
                App.alert({
                    container: $('.modal-body:first', $dialog),
                    place: 'prepend', // append or prepent in container
                    type: 'danger', // alert's typexxxx
                    message: _('검토 후 초대가능합니다.'),  // alert's message
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
                url: Flask.url_for('project._invite', {project_id: project_id}),
                data: {emails: data.join('\n')},
                success: function(data) {
                    App.alert({
                        // container: $('.modal-body', $dialog),
                        place: 'append', // append or prepent in container
                        type: 'success', // alert's typexxxx
                        message: data.message,  // alert's message
                        close: true, // make alert closable
                        reset: false, // close all previouse alerts first
                        focus: true, // auto scroll to the alert after shown
                        closeInSeconds: 5, // auto close after defined seconds
                        icon: 'fa fa-check' // put icon class before the message
                    });
                    $dialog.modal('hide');
                },
                error: function(data) {
                    // alert(data);
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
            return false;
        });
    };

    var handle_join2_action = function(project_id) {
        var $table = $('#user-search-table', $dialog);
        var $submit_btn = $('#user-search-table-selector', $dialog);
        $('form', $dialog).submit(function(e) {
            e.preventDefault();

        // $submit_btn.click(function(e) {
            // e.preventDefault();
            // console.log(e.relatedTarget);
            var data = $table.bootstrapTable('getSelections');
            data = $.map(data, function(row) {
                return row.user_email;
            });
            if (!data.length) {
                return false;
            }
            $('#emails', $dialog).val(data.join('\n'));
            // alert($('#emails', $dialog).val());

            // $.ajax({
            //     dataType: "json",
            //     method: "post",
            //     url: Flask.url_for('project._invite', {project_id: project_id}),
            //     data: {emails: data.join('\n')},
            //     success: function(data) {
            //         App.alert({
            //             // container: $('.modal-body', $dialog),
            //             place: 'append', // append or prepent in container
            //             type: 'success', // alert's typexxxx
            //             message: data.message,  // alert's message
            //             close: true, // make alert closable
            //             reset: false, // close all previouse alerts first
            //             focus: true, // auto scroll to the alert after shown
            //             closeInSeconds: 5, // auto close after defined seconds
            //             icon: 'fa fa-check' // put icon class before the message
            //         });
            //         $dialog.modal('hide');
            //     },
            //     error: function(data) {
            //         console.log(data);
            //         App.alert({
            //             container: $('.portlet-body:first', $dialog),
            //             place: 'prepend', // append or prepent in container
            //             type: 'danger', // alert's typexxxx
            //             message: data.responseJSON.message,  // alert's message
            //             close: true, // make alert closable
            //             reset: false, // close all previouse alerts first
            //             focus: true, // auto scroll to the alert after shown
            //             closeInSeconds: 5, // auto close after defined seconds
            //             icon: 'fa fa-check' // put icon class before the message
            //         });
            //     }
            // });
            // return false;
        });
    };

    return {
        init: function(project_id) {
            if (!project_id) {
                alert('project_id를 찾을 수 없습니다.');
            }
            handle_jquery_form_validation_rules(project_id);
            // handle_member_search_form(project_id);
            handle_form_validation(project_id);
            // handle_join_action(project_id); // 여러개 넣어서 초대하기
            handle_join2_action(project_id); // 선택해서 초대하기
        }
    };
}();
