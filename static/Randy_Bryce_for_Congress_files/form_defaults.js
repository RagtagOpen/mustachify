BSD.namespace('BSD.signup.admin');

BSD.signup.admin.getQueryParams = function () {
    var result = {};
    var tmp = [];

    bQuery.param.querystring()
        .split("&")
        .forEach(function (item) {
            tmp = item.split('=');
            result[tmp[0]] = decodeURIComponent(tmp[1]);
        });

    return result;
};

BSD.signup.admin.setDefaults = function (defaults) {
    bQuery.each(defaults, function (id, value) {
        var targetInput = bQuery('#' + id);
        var contents = targetInput.val();
        if (contents == undefined || contents == '') {
            targetInput.val(value);
        }
    });
};

BSD.signup.admin.addActionParams = function (actionParam) {
    var form = bQuery('#signup');
    var action = form.attr('action');
    form.attr('action', action + actionParam);
};

bQuery(document).ready(function () {
    // populate the form with approved query params
    bQuery.ajax({
        type: 'POST',
        url: '/ctl/Signup/AllowedParamsJson',
        data: BSD.signup.admin.getQueryParams(),
        success: function (data) {
            BSD.signup.admin.setDefaults(data['default_values']);
            BSD.signup.admin.addActionParams(data['form_action_string']);
        }
    });

});
