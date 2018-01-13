BSD.namespace('BSD.signup.admin');

BSD.signup.admin.spudSent = false;

bQuery(document).ready(function () {

    bQuery('#signup').submit(function (e) {

        var guid = bQuery.cookie('guid');
        if (typeof guid == 'string' && guid.length == 23) {
            bQuery('#_guid').val(guid);
        }

        if (!BSD.signup.admin.spudSent) {
            bQuery.bsd.spud('setFromForm', 'signup',
                [
                    'email',
                    'firstname',
                    'lastname',
                    'addr1',
                    'addr2',
                    'city',
                    'state_cd',
                    'zip',
                    'country',
                    'phone'
                ], function () {
                    BSD.signup.admin.spudSent = true;
                    setTimeout(function () {
                        bQuery('#signup').trigger('submit');
                    }, 300);
                });
            e.preventDefault();
        }
    });

    bQuery.bsd.spud('populateForm', 'signup',
        [
            'email',
            'firstname',
            'lastname',
            'addr1',
            'addr2',
            'city',
            'state_cd',
            'zip',
            'country',
            'phone'
        ]);
});
