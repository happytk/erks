

var actionSelectFormatter = function(value, row, _) {
    "use strict";

    console.log(value, row, _);

    var tmpl;
    tmpl = '<a class="btn btn-primary btn-xs btn-role-changer" href="' +
        '/p/' + row.id + '/_pgadmin' +
        '" data-toggle="modal" data-target="#project-pref-modal">설정</a>';
    return tmpl;
};

var ProjectGroupPreferenceProjects = function() {

    return {
        init: function() {
            var $table = $('#project-group-projects-table');
            $table.bootstrapTable();

            var $dialog = $('#project-pref-modal');
            $dialog.on('hide.bs.modal', function (event) {
                $table.bootstrapTable('refresh');
            });
        },
    };
}();