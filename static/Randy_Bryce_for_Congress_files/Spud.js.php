/*
 * BSD SPUD Plugin
 * A jQuery plugin to handle Spud/Personalization data via AJAX. Interfaces with
 * operation-specific endpoints to get and set data.  This file is generated
 * dynamically to reflect data provider settings and to reach the correct endpoint.
 */
(function($) {
    var methods = {
        /*
         * Set one of more value in SPUD
         *
         * @param fields object         Pairs of field names and field values to "set"
         * @param options object        Name-value pairs of jQuery.ajax options
         * @returns null
         */
        set: function( fields, options ) {
            // Handle setting any GUID passed back to us.
            options = options || {};
            options["success"] = function(a, b, c)
            {
                // Handle setting any GUID passed back here.
                if(typeof a == 'object' && 'guid' in a && 'cookieDomain' in a)
                {
                    $.cookie('guid', a.guid, {expires: 365, path: '/', domain: a.cookieDomain, secure: true});
                }
            };

            _makeRequest(
                _buildAjaxOptions(
                    "set",
                    {"mode": "standard", "fields": fields},
                    options
                )
            );
        },
        /*
         * Get one or more value from SPUD by name
         *
         * @param fields array          One or more fields to "get"
         * @param options object        Name-value pairs of jQuery.ajax options
         * @return null
         */
        get: function( fields, options ) {
            // Change this to a GET request for speed.
            options = options || {};
            options["type"] = "GET";

            _makeRequest(
                _buildAjaxOptions(
                    "get",
                    {"mode": "standard", "fields": fields},
                    options
                )
            );
        },
        /*
         * Set a custom value in SPUD
         *
         * @param appKey string         The custom prefix to use for this entry
         * @param name string           The name of this value
         * @param value mixed           The actual value
         * @param options object        Name-value pairs of jQuery.ajax options
         * @returns null
         */
        setCustom: function( appKey, fields, options ) {
            // Handle setting any GUID passed back to us.
            options = options || {};
            options["success"] = function(a, b, c)
            {
                if(typeof a == 'object' && 'guid' in a && 'cookieDomain' in a)
                {
                    $.cookie('guid', a.guid, {expires: 365, path: '/', domain: a.cookieDomain});
                }
            };

            _makeRequest(
                _buildAjaxOptions(
                    "set",
                    {"mode": "custom", "appKey": appKey, "fields": fields},
                    options
                )
            );
        },
        /*
         * Gets a custom value from SPUD
         *
         * @param appKey string         The custom prefix to use for this entry
         * @param name string           The name of the value
         * @param options object        Name-value pairs of jQuery.ajax options
         * @return null
         */
        getCustom: function( appKey, fields, options ) {
            // Change this to a GET request for speed.
            options = options || {};
            options["type"] = "GET";

            _makeRequest(
                _buildAjaxOptions(
                    "get",
                    {"mode": "custom", "appKey": appKey, "fields": fields},
                    options
                )
            );
        },
        /*
         * Given a form ID and array of fields populate it via SPUD
         *
         * @param formId string         String name of the form to populate
         * @param fields array          One or more fields to "get"
         * @param callback function     A callback
         * @return null
         */
        populateForm: function( formId, fields, callback ) {
            methods.get(fields, {
                success: function( data, textStatus, jqXHR ) {
                    $.each( data, function( name, value ) {
                        var targetInput = 'form#'+formId+' [name='+name+']';
                        var contents = $(targetInput).val();
                        if(contents == undefined || contents == '') {
                            $(targetInput).val(value);
                        }
                    });

                    if ( typeof callback == "function" ) {
                        callback();
                    }
                },
                "type": "GET"
            });
        },
        /* Given a form id and fields, set spud values from them. This is the
         * converse function of populateForm.
         *
         * @param formId string         String name of the form to fetch values from
         * @param fields array          One or more fields to "set"
         * @param callback function     A callback
         * @return null
         */
        setFromForm: function(formId, fields, callback) {
            var keyValues = {};
            for (var i = 0; i < fields.length; i++) {
                var field = fields[i];
                var formElement = bQuery("#" + formId + " [name=" + field + "]");
                if (formElement) {
                    keyValues[field] = formElement.val();
                }
            }
            methods.set(keyValues);

            if ( typeof callback == "function" ) {
                callback();
            }
        },
        /*
         * Given a share form ID and array of fields populate it via SPUD
         *
         * @param formId string         String name of the form to populate
         * @param fields array          One or more fields to "get"
         * @param callback function     A callback
         * @return null
         */
        populateShareForm: function( formId, fields, callback ) {
            methods.get(fields, {
                success: function( data, textStatus, jqXHR ) {
                    $.each( data, function( name, value ) {
                        var targetInput = 'form#'+formId+' [name='+'from_'+name+']';
                        var contents = $(targetInput).val();
                        if(contents == undefined || contents == '') {
                            $(targetInput).val(value);
                        }
                    });

                    if ( typeof callback == "function" ) {
                        callback();
                    }
                },
                "type": "GET"
            });
        },
        /* Given a share form id and fields, set spud values from them. This is the
         * converse function of populateForm.
         *
         * @param formId string         String name of the form to fetch values from
         * @param fields array          One or more fields to "set"
         * @param callback function     A callback
         * @return null
         */
        setFromShareForm: function(formId, fields, callback) {
            var keyValues = {};
            for (var i = 0; i < fields.length; i++) {
                var field = fields[i];
                var formElement = bQuery("#" + formId + " [name="+"from_"+field+"]");
                if (formElement) {
                    keyValues[field] = formElement.val();
                }
            }
            methods.set(keyValues);

            if ( typeof callback == "function" ) {
                callback();
            }
        }

    };

    var _buildAjaxOptions = function( slug, data, options ) {
        return $.extend(
            {},
            options || {},
            {
                "url": "/modules/spud/" + slug + ".php",
                "dataType": "jsonp",
                "type": options["type"] || "POST",
                "data": data
            }
        );
    }

    var _makeRequest = function( options ) {
        var response = $.ajax( options );

        if ( options.async === false ) {
            if ( response.status != 200 ) {
                $.error( 'jQuery.bsd.spud failed to make SPUD request' );
            }
        }
    }

    $.extend({
        bsd: $.extend($.bsd, {
            spud: function( method ) {
                if ( methods[method] ) {
                    return methods[method].apply( this, Array.prototype.slice.call( arguments, 1 ) );
                } else {
                    $.error( 'Method "' +  method + '" does not exist on jQuery.bsd.spud' );
                }
            }
        })
    });
})(window.bQuery || window.jQuery);
