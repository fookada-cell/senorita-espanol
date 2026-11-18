/* Visit and event counting with GoatCounter (free, no cookies, no personal data).
   To switch counting on or off, change GOATCOUNTER_CODE only.
   Empty string = counting off. Dashboard: https://<code>.goatcounter.com */
(function(){
  var GOATCOUNTER_CODE = "senoritachristina";
  window.sceTrack = function(name){
    try{ if(window.goatcounter && window.goatcounter.count) window.goatcounter.count({path:name, title:name, event:true}); }catch(e){}
  };
  if(!GOATCOUNTER_CODE) return;
  var s = document.createElement("script");
  s.async = true;
  s.src = "https://gc.zgo.at/count.js";
  s.setAttribute("data-goatcounter", "https://" + GOATCOUNTER_CODE + ".goatcounter.com/count");
  document.head.appendChild(s);
})();
