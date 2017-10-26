var btstrp_commonf_datetime = function(value, row, _) {
    if (value) {
        return moment(value).format("YYYY-MM-DD HH:mm");
    }
};


var btstrp_commonf_url_linker = function(value, row, _) {
    return '<a data-ajax="true" href="' + row.url + '">' + value + '</a>' +
        '<a data-ajax="true" data-target="_blank" href="' + row.url + '"><i class="fa fa-arrow-circle-o-down"></i></a>';
};

var btstrp_commonf_url_linker_no_ajax = function(value, row, _) {
    return '<a href="' + row.url + '">' + value + '</a>';
};

var btstrp_commonf_user = function(value, row, _) {
    return value;
};


var btstrp_commonf_checked = function(value, row, _) {
    if (row.rejected) {
        return '<i class="fa fa-ban"></i>';
    }
    else if (value) {
        return '<i class="fa fa-check"></i>';
    }
    else {
        return '-';
    }
};


var btstrp_commonf_actionurls = function(value, row, idx) {
    // console.log(row);
    var html = [];

    if (row.update_url) {
        html.push('<a data-ajax="true" class="btn btn-xs btn-primary" href="' +
          row.update_url +
        '">' + _('변경') + '</a>');
    }
        //url_for('.modify_infotype', infotype_id=infotype.id)
        //url_for('.delete_infotype', infotype_id=infotype.id)
    // if (!row.is_referred) {
    //     //html.push('<a class="btn btn-xs purple" href="{{}}" data-toggle="confirmation" data-original-title="Are you sure ?"><i class="fa fa-times"></i> {{_('삭제')}}</a>')
    //     html.push('<a class="btn btn-xs purple" href="' +
    //         row.delete_url +
    //       '"data-toggle="confirmation" data-original-title="Are you sure ?">' +
    //       '<i class="fa fa-times"></i>' + _('삭제') + '</a>');
    // }

    return html.join('');
};


function btstrp_f_term_name(value, row, index) {
    // return '<a href="' +Flask.url_for('term.term_view', {term_id: row.id}) + '">' + value + '</a>'
    var ret = '<a data-ajax="true" href="' + row.url + '">' + value + '</a>' +
        '<a data-ajax="true" data-target="_blank" href="' + row.url + '"><i class="fa fa-arrow-circle-o-down"></i></a>';

    if (row.is_ongoing) {
        if (row.requested_to_delete) {
            ret += ' <span class="label label-info">' + _('삭제의뢰중') + '</span>';
        }
        else if (row.requested_to_modify) {
            ret += ' <span class="label label-info">' + _('변경의뢰중') + '</span>';
        }
        else {
            ret += ' <span class="label label-info">' + _('신규의뢰중') + '</span>';
        }
    }
    return ret;
}

function btstrp_f_term_type(value, row, index) {
    var term_types = [];
    if (row._cls == "Term.UnitTerm") {
        term_types.push(_('표준단어'));
    }
    else if (row._cls == "Term.StrdTerm") {
        term_types.push(_('표준용어'));
    }
    else if (row._cls == "Term.Synonym") {
        term_types.push(_("금칙어"));
    }
    return term_types;
}


function hanldeTableToolbarRemoveButton($table) {
    var url = $table.data('url');
    var reload_on_delete_success = $table.data('reload-on-delete-success');
    // alert(reload_on_delete_success);
    $table.closest('.portlet-body').find('#remove-button').click(function(e) {
        e.preventDefault();

        var term_ids = $.map($table.bootstrapTable('getSelections'),
            function(obj, i) {
                return obj.id;
            });
        // alert(term_ids);
        var $button = $(this);
        if (term_ids.length) {

            swal({
                title: _("정말로 삭제하시겠습니까?"),
                text: _("삭제된 리소스는 다시 복구할 수 없습니다!"),
                type: "warning",
                showCancelButton: true,
                confirmButtonClass: "btn-danger",
                confirmButtonText: _("네, 지우겠습니다!"),
                cancelButtonText: _("아니요!"),
                closeOnConfirm: true,
            },
            function(){
                // $button.attr('disabled', 'disabled');
                App.blockUI({
                    target: $table.closest('.portlet-body'),
                    boxed: true,
                    overlayColor: 'red',
                    message: 'Deleting...'
                });

                $.ajax({
                    url: url,
                    type: 'DELETE',
                    contentType: 'application/json;charset=utf-8',
                    dataType: 'json',
                    data: JSON.stringify({
                        'ids': term_ids,
                    }),
                }).done(function(result) {
                    var message = '';
                    var swal_type = 'success';

                    if (result.deleted) {
                        message += gt.strargs('%1건이 삭제되었습니다.', result.deleted);
                    }
                    if (result.failed) {
                        message += gt.strargs('%1건이 참조관계 등의 이유로 삭제할 수 없습니다.', result.failed);
                        swal_type = 'warning';
                    }
                    App.unblockUI($table.closest('.portlet-body'));
                    swal("Your resource has been deleted.", message, swal_type);

                    if (reload_on_delete_success) {
                        // alert($table.closest('.portlet').find('.portlet-title > tools > a[class="reload"]'));
                        // console.log($table.closest('.portlet').find('.portlet-title > .tools > a[class="reload"]'), 'xxx');
                        $table.closest('.portlet').find('.portlet-title > .tools > a[class="reload"]').click();
                    }
                    else {
                        // swal("Your resource has been deleted.", message, swal_type);
                        $table.bootstrapTable('refresh');
                        // $table.bootstrapTable('resetView');
                        // $button.removeAttr('disabled');
                    }
                })
                .fail(function(result) {
                    alert(result);
                    App.unblockUI($table.closest('.portlet-body'));
                });
            });
        }
    });
}

// function hanldeTableToolbarRemoveButton($table) {
//     var url = $table.data('url-xls-upload');
// }
