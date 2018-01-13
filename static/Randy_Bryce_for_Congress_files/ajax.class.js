///
/// Functions to define in your script
///

/*

REQUIRED HANDLER FUNCTIONS:
It's required that you define these when creating the class, or explicitly set them to 'none'

success_handler( response, ajax_request)
	If ajax completes successfully, then this function is called to handle the response.
		* response - will either be the http.responseText or the http.responseXML depending on response_type
		* ajax_request - reference to the ajax_class object

failure_handler( message, error_code, ajax_request)
	If ajax was unsuccessful, call this function to gracefully handle an error.  Critical errors like an invalid
	ajax_url are also run through here but will display in an alert if this function is not present.  If not defined,
	then nothing is displayed.
		* message - the failure message; contains no formatting
		* error_code - if not 0, then prints the HTTP Error code and related help
		* ajax_request - reference to the ajax_class object


OPTIONAL HANDLER:
The class will call a function if one is defined:

display_processing_message( on_off, ajax_request)
	You want to give a visual que to the user that a connection is being made.  If this function is defined,
	it will toggle that que on and off as appropriate automatically.  You're function handles the mechanics.
	If not defined, then nothing is displayed.
		* on_off - 'on' turns the indicator on; 'off' to turn it off
		* ajax_request - reference to the ajax_class object


References:
http://developer.apple.com/internet/webcontent/xmlhttpreq.html
http://www.xulplanet.com/references/objref/XMLHttpRequest.html
http://www.whatwg.org/specs/web-apps/current-work/#scripted-http

*/


///
/// an external helper function that returns true/false depending if the user's browser is AJAX aware
///   it's not necessary to pass it any params
///
function ajax_check_enabled( params)
{
	if (params == null)
	{
		params = {
				success_handler : 'none',
				failure_handler : 'none'
				} ;
	}
	else
	{
		params.success_handler = (params.success_handler) ? params.success_handler : 'none' ;
		params.failure_handler = (params.failure_handler) ? params.failure_handler : 'none' ;
	}

	var ajax = new ajax_class( params) ;
	return ajax.check_ajax_enabled() ;
}


///
/// class constructor
///
function ajax_class( params)
{
	// if params is not defined, then define it with some bogus filler
	if ((params == undefined) || (!params))
	{
		params = {} ;
	}

	// connection specifics
	this.ajax_url = (params.ajax_url) ? params.ajax_url : 'foo' ;		// url we're connecting to
	this.timeout = (params.timeout) ? params.timeout : 5000 ;			// how long to try for (think slow queries, etc)
	this.method = (params.method) ? params.method : 'GET';				// make a POST or GET connection
	this.post_vars = (params.post_vars) ? params.post_vars : null ;		// the POST vars to send (ie. foo=bar&cow=moo); be sure to escape when needed...
																		//    post_vars : "foo=bar&a_string=" + escape('Smith & Jones')
	this.query_hash = '' ;												// do not override!  a cache busting hash
	this.version = '12/8/2005' ;										// only used when sending a custom header; not critical at all


	// processing specifcs
	this.response_type = (params.response_type) ? params.response_type : 'text' ;	// looking for text or xml?
	this.extended_data = (params.extended_data) ? params.extended_data : null ;		// a member the dev can use to supply custom datas
	this.request = null ;															// the full xmlhttprequest object
	this.completed_request = false ;						// do not override! - a toggle so we now our current state - needed for timeout


	// debug params
	this.ajax_debug = (params.ajax_debug) ? params.ajax_debug : false ;			// display debugging messages
	this.test_no_ajax = (params.test_no_ajax) ? params.test_no_ajax : false ;	// sim browser without ajax
	this.test_timeout = (params.test_timeout) ? params.test_timeout : false ;	// sim exceeding timeout setting
	this.test_permission_denied = (params.test_permission_denied) ? params.test_permission_denied : false ;	// url out of scope (Mozilla problem only)
	this.test_http_404 = (params.test_http_404) ? params.test_http_404 : false;	// sim connecting to an invalid page


	// define what the expected help functions external to the class will be - set some defaults that can be overridden
	this.success_handler = determine_handler( params.success_handler, 'success') ;
	this.failure_handler = determine_handler( params.failure_handler, 'failure') ;
	this.display_processing_message = params.display_processing_message ;
}


///
/// make sure required handler are defined, or at least set to 'none'; throw an error if they are not defined
///
function determine_handler( param_handler_setting, type)
{
	if (param_handler_setting)
	{
		return (param_handler_setting == 'none') ? null : param_handler_setting ;
	}
	// neither a custom or global handler is defined, so set to null
	else
	{
		throw new Error("ERROR: undefined " + type + " handler function.  AJAX connection not established") ;
	}
}



///
/// we need to see if AJAX is available, and if so, set it up the request object
///   I don't recall where I lifted this bit of code from, but it's fairly common
///
ajax_class.prototype.getHTTPObject = function()
{
	// ajax test: if we are testing no ajax fallback, then make it look like ajax is not available
	if (this.test_no_ajax)
	{
		if (this.ajax_debug) alert('ajax test: simulating AJAX is not available') ;
		return false ;
	}


	// first attemp at creating the XMLHTTP object; this is for MSIE
	var xmlhttp = false;
	if(typeof ActiveXObject!='undefined' && ActiveXObject)
	{
    	try
    	{
    		xmlhttp = new ActiveXObject("Msxml2.XMLHTTP");
    	}
    	catch (e)
    	{
    		try
    		{
    			xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
    		}
    		catch (E)
    		{
    			xmlhttp = false;
    		}
    	}
    }

	// if it failed or got undesired results, try again; this is for MOZ
	if (!xmlhttp && typeof XMLHttpRequest != 'undefined')
	{
		try
		{
			xmlhttp = new XMLHttpRequest();
		}
		catch (e)
		{
			xmlhttp = false;
		}
	}


	// return the results
	return xmlhttp;
}



///
/// see if we can establish an XMLHTTP object; we only want to call this memnber once per page load - it's called
///   if you want to implement a no-ajax fallback
///
ajax_class.prototype.check_ajax_enabled = function()
{
	var temp_xmlhttp = this.getHTTPObject() ;
	return ((!temp_xmlhttp) ? false : true) ;
}



///
/// hanlde the call FROM the client script and do it's bidding!  This is where the connection is made
///
ajax_class.prototype.comm_with_server = function ()
{
	///
	/// notes:
	///		+ it's up to the developer to make sure the URL is correct
	///		+ it's highly recommended that you use a relative path (like foo.php) so you don't have to worry about permissions
	///			(as with http//www.bar.com/ vs. http://bar.com or even vs. https//www.bar.com)
	///		+ it's probably a good idea to escape data being included in query params; for example you'd want this...
	///			ajax_url : some_url + "?foo=bar&a_string=" + escape('Smith & Jones')
	///


	// ajax test: make an invalid url on purpose
	if (this.test_http_404)
	{
		this.ajax_url = '/some_invalid_page' ;

		if (this.ajax_debug) alert('ajax test: forcing http 404 [' + this.ajax_url + ']') ;
	}


	// we're going in, so start the loading indicator if defined
	if (this.display_processing_message)
	{
		this.display_processing_message( 'on', this) ;
	}


	// assign our ajax object to a local variable so that our onreadystatechange can maintain scope of the object
	var ajax_request = this ;


	// ajax test: send them to a URL they don't have access to
	if (this.test_timeout)
	{
		if (this.ajax_debug)
		{
			alert('ajax test: simulating timeout') ;
		}

		// force the time out for very soon
	    window.setTimeout( function() { ajax_check_timeout( ajax_request) }, 100);
	    return ;
	}

	// set a timeout to protect us from oddball situations like slow servers
    window.setTimeout( function() { ajax_check_timeout( ajax_request) }, this.timeout);



    ///
    /// make the xmlhttprequest object
    ///

    // make the object - if we didn't get a request object then dump b/c ajax is not available
    var request = this.getHTTPObject() ;
    this.request = request ;
	if (!request)
	{
		this.handle_critical_error('AJAX is not available.  Could not create an HTTPObject.') ;
		return ;
	}


	// modify the url to add a unique hash so that we bust client-side caching on IE (pretty much)
	//   - http://en.wikipedia.org/wiki/XMLHttpRequest#Microsoft_Internet_Explorer_Cache_issues
	this.query_hash = ((this.ajax_url.indexOf('?') == -1) ? '?' : '&') + 'hash=' + (Math.floor((Math.random()*10000)+1)) ;
	var full_request_url = this.ajax_url + this.query_hash;


	// ajax test: send them to a valid URL but on a different server
	if (this.test_permission_denied)
	{
		full_request_url = 'http://www.spellingcow.com/' ;
		if (this.ajax_debug) alert('ajax test: forcing permission denied to our of scope URL (NOTE: this is only a problem for Mozilla)') ;
	}

	// make the connection - On at least IE6, failure to create the object is a fatal error and will break the page
	//   so catch the error and handle it gracefully
	if (this.ajax_debug) alert('DEBUG: connecting to [' + full_request_url + '] via [' + this.method + ']') ;
	try
	{
		request.open( this.method, full_request_url, true);
	}
	catch (error)
	{
		this.handle_critical_error('Could not connect to AJAX server.  Please try again later.') ;
		return ;
	}

	// add a custom header, a little wink at the server
	request.setRequestHeader('X-Requested-With', 'BSD AJAX, revision ' + this.version) ;

	// for POST method we need to state the content type
	if (this.method == 'POST')
	{
		request.setRequestHeader("Content-Type","application/x-www-form-urlencoded") ;
	}


	// due to my lack of js referencing knowledge, this is the only way I can think to have a statechange function where I can
	//   pass the ajax class object I want without it losing scope
	request.onreadystatechange = function() {
		// 4 = complete (3=interactive (sucks on IE); 2=loaded; 1=loading; 0=unitialized)
		//	http://jpspan.sourceforge.net/wiki/doku.php?id=javascript:xmlhttprequest:behaviour
		if (request.readyState == 4)
		{
			// mark that we've got a successful return
			ajax_request.completed_request = true ;

			// turn off the processing indicator
			if (ajax_request.display_processing_message)
			{
				ajax_request.display_processing_message( 'off', ajax_request) ;
			}

			// 200 = OK.... everything else is a problem to us
			//	http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
			if (request.status == 200)
			{
				// use the success handler if one is defined; send the desired response format
				if (ajax_request.success_handler)
				{
					var response = (ajax_request.response_type == 'xml') ? request.responseXML : request.responseText ;
					ajax_request.success_handler( response, ajax_request) ;
				}
			}
			// we have a bad status so handle the error
			else
			{
				// if we're in debug mode, state the error
				if (ajax_request.debug)
				{
					alert('Failed: [' + request.status + '] - ' + request.statusText) ;
				}

				// there was some error so use the fail function if there is one defined
				if (ajax_request.failure_handler)
				{
					ajax_request.failure_handler( request.statusText, request.status, ajax_request) ;
				}
			}
		}
	};

	// send POST query params (will be NULL for GET)
	request.send( this.post_vars);
}


///
/// called by the comm_with_server function; generally means the developer screwed up the ajax_url
///
ajax_class.prototype.handle_critical_error = function( message)
{
	// stop processing on this connection
	this.completed_request = true ;

	// turn off the indicator
	if (this.display_processing_message)
	{
		this.display_processing_message( 'off', this) ;
	}

	// let the caller handle the error
	if (this.failure_handler)
	{
		this.failure_handler( message, 0, this) ;
	}
	// if the dev is in debug mode, then alert them to this
	else if (this.ajax_debug)
	{
		alert( message);
	}
}


///
/// NOT a class member!  It is called from the class though.  In the event of a slow server, client connection dieing,
///   or some other wierdness, this is our saving throw.  Because of the way settimeout works, this needs to be outside of the class
///
function ajax_check_timeout( ajax_request)
{
	// only timeout if we are still processing
	if (!ajax_request.completed_request)
	{
		// stop processing on this connection
		ajax_request.completed_request = true ;

		// turn off the indicator
		if (ajax_request.display_processing_message)
		{
			ajax_request.display_processing_message( 'off', this) ;
		}

		// throw a nice error
		if (ajax_request.failure_handler)
		{
			ajax_request.failure_handler( 'The request to the server exceeded the timeout setting.', 0, ajax_request) ;
		}
	}
}
