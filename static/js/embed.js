(function() {
  'use strict';

  var html = document.getElementsByTagName('html')[0];
  var script = (function() {
    var scripts = document.getElementsByTagName('script');
    return scripts[scripts.length - 1];
  })();
  var iframe = document.createElement('iframe');
  var a = document.createElement('a');
  var qs = '';
  var utmParams = {
    source: (/(^|&|\?)utm_source=([^&]+|\b)/.exec(window.location.search) || []).slice(-1)[0] || null,
    medium: (/(^|&|\?)utm_medium=([^&]+|\b)/.exec(window.location.search) || []).slice(-1)[0] || null,
    campaign: (/(^|&|\?)utm_campaign=([^&]+|\b)/.exec(window.location.search) || []).slice(-1)[0] || null
  };
  var params = ['embedded=1'];
  params.push('origin=' + encodeURIComponent(document.location.href));
  for (var utmParam in utmParams) {
    if (utmParams[utmParam]) {
      params.push('utm_' + utmParam + '=' + encodeURIComponent(utmParams[utmParam]));
    }
  }
  qs = params.length ? qs + '?' : '';
  params = params.join('&');
  qs = qs + params;

  iframe.frameborder = 0;
  iframe.width = 1;
  iframe.height = 300;
  iframe.marginheight = 0;
  iframe.marginwidth = 0;
  iframe.scrolling = 'no';
  iframe.src = 'https://ironstache.herokuapp.com/' + qs;
  iframe.id = 'mustachify-embed';
  iframe.style = 'width: 1px; min-width: 100%; border: none;';

  a.href = script.src;

  function getHost(loc) {
    var link = document.createElement('a');
    link.href = loc;
    return link.protocol + '//' + link.hostname + (link.port && ((link.protocol === 'http:' && link.port !== '80') || (link.protocol === 'https:' && link.port !== '443')) ? ':' + link.port : '');
  }

  window.addEventListener('message', function(message) {
    try {
      window.console.debug('message received', message);
    } catch (err) {}

    if (message.origin !== getHost(iframe.src)) {
      return;
    }

    var data = message.data;
    if (data && typeof data === 'string') {
      data = JSON.parse(data);
    }
    if (data && typeof data.height !== 'undefined') {
      iframe.height = data.height;
    }
    if (data && data.scrollToTop) {
      var obj = iframe,
        iframeTop = 0;
      if (iframe.offsetParent) {
        do {
          iframeTop += obj.offsetTop;
          obj = obj.offsetParent;
        } while (obj);
      }
      html.scrollTop = iframeTop;
      body.scrollTop = iframeTop;
    }
  });

  script.parentNode.insertBefore(iframe, script);
})();
