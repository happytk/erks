
var _detailed_modal = function($button, $modal, target) {
  var puid = $button.data('project-user-id');
  var can_manage_all = $button.data('can-manage-all');
  var $can_manage_all_checkbox = $('#can-manage-all', $modal);
  var $table = $('table', $modal);
  var $table_wrapper = $('#table-wrapper', $modal);

  $table.bootstrapTable({
        url: "/api_btstptbl/projectuser/"+puid+"/"+target,
        pagination: "true",
        pageSize: "10",
        search: true,
        maintainSelected: true,
        clickToSelect: true,
  });

  // console.log(can_manage_all, $can_manage_all_checkbox);
  $can_manage_all_checkbox.prop('checked', can_manage_all).change();
  if (can_manage_all) {
      $table_wrapper.hide();
  } else {
      $table_wrapper.show();
  }

  var changer = function(e) {
      e.preventDefault();
      console.log('change', e);
      // $table_wrapper.toggle();
      if ($can_manage_all_checkbox.prop('checked')) {
        $table_wrapper.hide();
      }
      else {
        $table_wrapper.show();
      }
  };
  // $can_manage_all_checkbox.unbind("change", changer);
  $can_manage_all_checkbox.change(changer);
  console.log($can_manage_all_checkbox);

  $('.red', $modal).unbind( "click" );
  $('.red', $modal).click(function(e) {
        e.preventDefault();

        var manageable_ids = $.map($table.bootstrapTable('getAllSelections'), function(v, i) {
            return v.id;
        });
        var data = {};

        data['manageable_'+target] = manageable_ids.join();
        data['can_manage_all_'+target] = $can_manage_all_checkbox.prop('checked');

        console.log(data);

        $.ajax({
            url: "/api_btstptbl/projectuser/"+puid+"/"+target,
            method: "post",
            data: data,
        }).done(function(msg) {
            // $table.bootstrapTable('refresh');
            $button.data('can-manage-all', $can_manage_all_checkbox.prop('checked'));
            App.alert({
                container: $('.modal-body', $modal), // alerts parent container
                place: 'prepend', // append or prepent in container
                type: 'success', // alert's typexxxx
                message: gt.gettext('성공적으로 저장되었습니다.'),  // alert's message
                close: true, // make alert closable
                reset: false, // close all previouse alerts first
                focus: true, // auto scroll to the alert after shown
                closeInSeconds: 5, // auto close after defined seconds
                icon: 'fa fa-check' // put icon class before the message
            });
        });
  });
};

function memberTableSearchQuery(params) {
    var formArray = $("#member-search-form").serializeArray();
    for (var i = 0; i < formArray.length; i++){
        // console.log(formArray[i]['name'], formArray[i]['value']);
        // params[formArray[i]['name']] = formArray[i]['value'];
        params[formArray[i].name] = formArray[i].value;
    }
    // params['foo']=1;
    // params['bar']=2;
    return params;
}

$('#role-changer-modal').on('hide.bs.modal', function(event) {
    // var button = $(event.relatedTarget);
    console.log(event);
    // alert(button.closest('tr').data('uniqueid'));
    var $table = $('#project-user-table');
    $table.bootstrapTable('refresh');
});

$('#detailed-model-modal').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget); // Button that triggered the modal
    var modal = $(this);
    _detailed_modal(button, modal, 'models');
});

$('#detailed-glossary-modal').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget); // Button that triggered the modal
    var modal = $(this);
    _detailed_modal(button, modal, 'glossaries');
});

var handleDetailedRoleChanger = function(params) {
    console.log(params.data);
    // just use setTimeout
    setTimeout(function () {
        params.success([{
                "id": 0,
                "glossary": { "glossary_name": "hello" },
            }, {
                "id": 1,
                "glossary": { "glossary_name": "helloworld" }
            }]);
    }, 1000);
};

var actionFormatter = function(value, row, _) {
    var tmpl = '';
    if (value) {
    }
    else {
        if (row._cls != 'ProjectUserBase.ProjectUser') {
            tmpl = '<button class="btn btn-sm red execute-action" disabled>' + gt.gettext('실행') + '<i class="fa fa-check"></i></button>';
            return tmpl;
        }
    }
};

var roleChangerFormatter = function(value, row, _) {
    var tmpl;
    if (value) { //if you're owner-row, do nothing.
    }
    else {
        if (row._cls == 'ProjectUserBase.ProjectWaitingUserOutbound') {
            tmpl = '<select class="form-control input-sm">' +
                '<option value="">ACTIONS..</option>' +
                '<option value="resend">' + gt.gettext('초대메일 재발송') + '</option>' +
                '<option value="cancel_invitation">' + gt.gettext('초대 취소') + '</option>' +
                '</select>';
            return tmpl;
        }
        else if (row._cls == 'ProjectUserBase.ProjectWaitingUserInbound') {
            tmpl = '<select class="form-control input-sm">' +
                '<option value="">ACTIONS..</option>' +
                '<option value="approve">' + gt.gettext('초대 승인') + '</option>' +
                '<option value="reject">' + gt.gettext('초대 거절') + '</option>' +
                '</select>';
            return tmpl;
        }
        else if (row._cls == 'ProjectUserBase.ProjectUser') {
            // 여기서 template의 필요를 느낀다.
            // 탈퇴처리는 어디서?
            tmpl = '<a class="btn btn-xs red btn-role-changer" href="' +
                '/pu/' + row.id + '/_role_changer' +
                //Flask.url_for('project._user_role_changer', project_user_id=row.id) +
                '" data-toggle="modal" data-target="#role-changer-modal">' + gt.gettext('권한설정') + ' <i class="fa fa-check"></i></a>';
            return tmpl;
        }
    }
};

var roleFormatter = function(value, row, _) {
    var tmpl = '';
    if (row._cls == 'ProjectUserBase.ProjectWaitingUserOutbound') {
        if (row.is_expired) {
            return gt.gettext('초대(expired)');
        }
        else {
            return gt.strargs('초대중(%1회 메일발송)', row.outbound_email_sent_count);
        }
    }
    else if (row._cls == 'ProjectUserBase.ProjectUser') {

        if (row.is_modeler) {
            tmpl += gt.gettext('<b><u>모델러</u></b> ');
        }
        if (row.is_termer) {
            tmpl += gt.gettext('<b><u>용어관리자</u></b> ');
        }
        if (row.is_owner) {
            tmpl += gt.gettext('<b><u>프로젝트관리자</u></b> ');
        }
        if (!tmpl.length) {
            return gt.gettext('일반사용자');
        }
        else {
            return tmpl;
        }
    }
    else if (row._cls == 'ProjectUserBase.ProjectWaitingUserInbound') {
        return gt.gettext('가입요청중');
    }
    else {
        return 'unknown';
    }
};

var Members = function() {

    var handleDetailedRoleChanger = function() {
        // var $table = $('#project-user-role-changer-table');
        // console.log('detailed-role-action-table on');
        // $table.bootstrapTable({
        //     //project-user
        //     ajax: function(params) {
        //         console.log(params.data);
        //         // just use setTimeout
        //         setTimeout(function () {
        //             params.success([{
        //                     "id": 0,
        //                     "glossary": { "glossary_name": "hello" },
        //                 }, {
        //                     "id": 1,
        //                     "glossary": { "glossary_name": "helloworld" }
        //                 }]);
        //         }, 1000);
        //     }
        // });
    };

    var handleMemberSearchTable = function() {

        var $table = $('#project-user-table');

        $('#search', $("#member-search-form")).on('click', function(e) {
            e.preventDefault();
            $table.bootstrapTable('refresh');
        });
    };



    var handleSearch = function() {
        var $table = $('#project-user-table');
        var project_id = $table.data('project-id');
        var target = $('#project-user-table');

        console.log('member-on', project_id, target);
        if (!project_id) {
            alert('no_project_id');
            return;
        }

        target.on('change', 'select', function() {
            var $tr = $(this).closest('tr'),
                selected = $tr.find('select').val();
            if (selected) {
                $tr.find('.execute-action').removeAttr('disabled');
            } else {
                $tr.find('.execute-action').attr('disabled', 'disabled');
            }
        });

        target.on('click', '.invite-action', function() {
            var $tr = $(this).closest('tr'),
                user_id = $tr.find('input[name="user_id"]:first').val(),
                url = Flask.url_for('project.member_role_action', {project_id: project_id});
            $.ajax({
                type: 'POST',
                url: url,
                data: {user_id: user_id, action: 'invite_member'},
                success: function(msg) {
                    $tr.empty().append(msg);
                },
                error: function(msg) {
                    alert(msg);
                },
            });
        });

        //권한 상세설정 btn을 눌렀을 경우
        // target.on('click', '.btn-role-changer', function() {
        //     var $tr = $(this).closest('tr'),
        //         project_user_id = $tr.data('uniqueid');
        //     $('#role-changer-modal').modal('show');
        // });

        target.on('click', '.execute-action', function() {
            var $tr = $(this).closest('tr'),
                selected = $tr.find('select').val(),
                project_user_id = $tr.data('uniqueid'),
                url = null,
                role = null,
                action = null;

            if (!project_user_id) {
                console.log('no-project_user_id');
            }
            else {
                console.log('project-user-id', project_user_id);
            }

            url = Flask.url_for('project.member_role_action', {
                project_id: project_id,
            });
            $.ajax({
                type: 'POST',
                url: url,
                data: {
                    project_user_id: project_user_id,
                    action: selected,
                },
                success: function(msg) {
                    //$tr.empty().append(msg);
                    console.log(msg.id);
                    console.log(msg);
                    console.log(selected);
                    if (selected == 'reject') {
                        $table.bootstrapTable('removeByUniqueId', project_user_id);
                    }
                    else {
                        $table.bootstrapTable('updateByUniqueId', {
                            id: project_user_id, row: msg
                        });
                    }
                },
                error: function(msg) {
                    console.log(msg);
                },
            });
        });

        // $('#btn_member_search_waiting').click(function() {
        //     var url = Flask.url_for('project.member_search', {project_id: project_id}) + '?only=waiting';
        //     target.empty().load(url, function() {});
        // });

        // $('#btn_member_search_invited').click(function() {
        //     var url = Flask.url_for('project.member_search', {project_id: project_id}) + '?only=invited';
        //     target.empty().load(url, function() {});
        // });

        $('#user-search-btn').click(function() {
            $.post(Flask.url_for('project._members', {project_id: project_id}), {
                    search_text: $('#user-search').val(),
                },
                function(resp) {
                    target.closest('.portlet-body').empty().append($(resp));
                });
        });
    };

    return {
        // main function to initiate the module
        init: function() {
            handleMemberSearchTable();
            handleSearch();
            handleDetailedRoleChanger();
        },
    };
}();
