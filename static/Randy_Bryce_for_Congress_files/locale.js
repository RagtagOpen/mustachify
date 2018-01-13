
YAHOO.util.Event.onDOMReady(
    function(){
        var signup_locale = new locale({});
        
        //this custom event fires after SPUD loads data
        LOCALE_COUNTRY_LISTENER = new YAHOO.util.CustomEvent('blue_country_event');
        LOCALE_COUNTRY_LISTENER.subscribe( function(){ signup_locale.load(true); }, signup_locale);
        
        YAHOO.util.Event.addListener(signup_locale.get_country(),"change",
            function(e,signup_locale){ signup_locale.load(); }, signup_locale, true);
        

            // add a listener to deal with region level postal exceptions
        if(signup_locale.region_postal_exceptions.length > 0){
            YAHOO.util.Event.addListener('state_cd','change',signup_locale.handle_postal_exceptions,signup_locale);
        }
        

    }
);
