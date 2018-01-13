(function() {
    var oldOnload = window.onload || function() {};

    window.onload = function() {
        oldOnload();
        
        document.getElementById('signup').onsubmit = function() {
            document.getElementsByName('submit-btn')[0].disabled = true;
        };
    };
})();
