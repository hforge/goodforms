if (!Array.prototype.indexOf) {
    Array.prototype.indexOf = function (searchElement /*, fromIndex */ ) {
        "use strict";
        if (this == null) {
            throw new TypeError();
        }
        var t = Object(this);
        var len = t.length >>> 0;
        if (len === 0) {
            return -1;
        }
        var n = 0;
        if (arguments.length > 1) {
            n = Number(arguments[1]);
            if (n != n) { // shortcut for verifying if it's NaN
                n = 0;
            } else if (n != 0 && n != Infinity && n != -Infinity) {
                n = (n > 0 || -1) * Math.floor(Math.abs(n));
            }
        }
        if (n >= len) {
            return -1;
        }
        var k = n >= 0 ? n : Math.max(len - Math.abs(n), 0);
        for (; k < len; k++) {
            if (k in t && t[k] === searchElement) {
                return k;
            }
        }
        return -1;
    }
}


function switch_input(input, dep_name, dep_value) {
    /* Disable/Enable text field if dep_value ON changed */
    var dep_name2 = "field_" + dep_name;
    var item = $("input[name="+dep_name+"],textarea[name="+dep_name+"]");
    var item2 = $("input[name="+dep_name+",select[name="+dep_name+"]");
    var item3 = $("input[name="+dep_name+",option[name="+dep_name+"]");
    var item4 = $("input[name="+dep_name+",div[id="+dep_name2+"]");
    var type = input.attr('type');

    if (type == 'radio') {
        /* RADIO : value True if 1 */
        if (input.val() == 1){
            item.removeAttr("disabled");
            item2.removeAttr("disabled");
	    item3.removeAttr("disabled");
	    item4.removeAttr("disabled");
            item.removeClass("disabled");
            item2.removeClass("disabled");
	    item3.removeClass("disabled");
	    item4.removeClass("disabled");
            item.trigger('change');
        }
        else {
            item.attr("disabled", "true");
            item2.attr("disabled", "true");
	    item3.attr("disabled", "true");
	    item4.attr("disabled", "true");
            item.addClass("disabled");
            item2.addClass("disabled");
	    item3.addClass("disabled");
	    item4.addClass("disabled");
        }
    }
    else {
        /* OPTION : value ON if value == dep_value */
        if (input.val()== dep_value){
            if (input.attr('checked')){
                item.removeAttr("disabled");
                item.removeClass("disabled");
                item4.removeAttr("disabled");
                item4.removeClass("disabled");
            }
            else {
                item.attr("disabled", "true");
                item.addClass("disabled");
                item4.attr("disabled", "true");
                item4.addClass("disabled");
            }
        }
    }
}

function getElementsByClass( searchClass, domNode, tagName) {
    if (domNode == null) domNode = document;
    if (tagName == null) tagName = '*';
    var el = new Array();
    var tags = domNode.getElementsByTagName(tagName);
    var tcl = " "+searchClass+" ";
    for(i=0,j=0; i<tags.length; i++) {
	var test = " " + tags[i].className + " ";
	if (test.indexOf(tcl) != -1)
	    el[j++] = tags[i];
    }
    return el;
}

function getElementsById( searchId, domNode, tagName) {
    if (domNode == null) domNode = document;
    if (tagName == null) tagName = '*';
    var el = new Array();
    var tags = domNode.getElementsByTagName(tagName);
    for(i=0,j=0; i<tags.length; i++) {
	if (tags[i].getAttribute("id") == searchId){
	    el[j++] = tags[i];}
    }
    return el;
}

function find_previous_ind(arr, elem){
    for (var i = 0; i < arr.length; i++){
	if (elem.charAt(7) == arr[i].charAt(7) &&
	    parseInt(elem.substring(8, 10), 10) == parseInt(arr[i].substring(8, 10), 10) + 1 &&
	    elem.substring(10, 12) == arr[i].substring(10, 12)){
	    return i;
	}
    }

    return -1;
}

function is_empty(elem, arr){
    switch(elem.tagName){
    case "TEXTAREA":
	if (elem.value == null || elem.value == ""){
	    return true;}
	return false;
	break;
    case "INPUT":
	if (elem.getAttribute('type') != 'radio'){
	    if (elem.value == null || elem.value == ""){
		return true;}
	    return false;}
	else {
	    for (var i = 0; i < arr.length; i++){
		if (arr[i].getAttribute('checked') == 'checked'){
		    return false;}}
	    return true;}
	break;
    case "SELECT":
	if (elem.selectedIndex == 0){
	    return true;}
	return false;
	break;
    case "DIV":
	var subs = elem.getElementsByTagName('input');
	for (var i = 0; i < subs.length; i++){
	    if (subs[i].getAttribute('checked') == 'checked'){
		return false;}}
	return true;
	break;
    default:
	return false;
    }
}

function empty_line(id){
    for (var i = 0; i < 10; i++){
	var test_id = id.substring(0, 11) + i;
	var elem = getElementsById(test_id)[0];

	if (typeof elem == 'undefined'){
	    continue;}

	if (is_empty(elem, [])){
	    continue;}

	return false;
    }

    return true;
}


function hide_multilines() {
    var elems = getElementsByClass('field-widget');
    var multilines = new Array();
    var multilines_shown = new Array();

    for (var i = 0; i < elems.length; i++){
	// Catch textarea
	var sub_elem = elems[i].getElementsByTagName('textarea')[0];
        // if not, catch div
        if (typeof sub_elem == 'undefined'){
           sub_elem = elems[i].getElementsByTagName('div')[1];
           if (typeof sub_elem != 'undefined' && sub_elem.getAttribute("id") == null){
              sub_elem = elems[i].getElementsByTagName('textarea')[0];}}
	// If not catch input
	if (typeof sub_elem == 'undefined'){
	    sub_elem = elems[i].getElementsByTagName('input')[0];}
	// If not, catch select
	if (typeof sub_elem == 'undefined'){
	    sub_elem = elems[i].getElementsByTagName('select')[0];}

	// If not, don't do anything
	if (typeof sub_elem == 'undefined'){
	    continue;}


	var id = sub_elem.getAttribute("id");
	if (id == null){
	    continue;}
	var tmp = elems[i].getElementsByTagName('input');

	// only handle multi-lines
	if (id.charAt(6) != '_'){
	    continue;}

	var ind = find_previous_ind(multilines, id);
	//alert(id + " " + ind);
	// deal with first and new multi-line
	if (ind == -1){
	    multilines.push(id);
	    multilines_shown.push(true);


	    if (is_empty(sub_elem, tmp)){
            // if (sub_elem.value == null || sub_elem.value == ""){
		multilines_shown[multilines_shown.length - 1] = false;
	    }

	    // insert button
	    if ((id.charAt(11) == '0')||
		multilines.indexOf(id.substring(0,11) + parseInt(id.charAt(11) - 1)) == -1){
		var b = document.createElement("input");
		b.type = "button";
		b.value = "+";
		b.className = "mbutton";
		b.setAttribute('onclick', "show_next_line('" + id + "');");
		//elems[i].appendChild(b);}
		elems[i].insertBefore(b, elems[i].firstChild);}
	    continue;
	}

	var upline = parseInt(id.substring(8, 10), 10) - 1;

	if (upline < 10){
	    upline = id.substring(0, 8) + '0' + upline + '00';}
	else {
	    upline = id.substring(0, 8) + upline + '00';}
	if (! empty_line(upline)){
	    multilines[ind] = id;
	    multilines_shown[ind] = false;
	    continue;}

	// Easy case: last one seen is hidden
	if (multilines_shown[ind] == false){
	    multilines[ind] = id;
	    elems[i].setAttribute('style', 'display:none');
	}

	// Tricky : last not hidden + no value, last shown
	if (is_empty(sub_elem, tmp)){
	    // if (sub_elem.value == null || sub_elem.value == ""){
	    multilines[ind] = id;
	    multilines_shown[ind] = false;
	    //elems[i].setAttribute('style', 'display:none');
	    continue;}

	multilines[ind] = id;
	if (sub_elem.value == 'undefined' && sub_elem.value == ''){
	    elems[i].setAttribute('style', 'display:none');}
    }
}

function show_next_line(id){
    var elems = getElementsByClass("field-widget");
    var id_bis = id;

    for (var i = 0; i < elems.length; i++){
    	// Catch textarea
    	var sub_elem = elems[i].getElementsByTagName('textarea')[0];
    	// If not catch input
    	if (typeof sub_elem == 'undefined'){
    	    sub_elem = elems[i].getElementsByTagName('input')[0];}
	// Skip button ...
	if (typeof sub_elem != 'undefined'
	    && sub_elem.getAttribute('type') == 'button'){
	    sub_elem = elems[i].getElementsByTagName('input')[1];}
	// If not, catch select
	if (typeof sub_elem == 'undefined'){
	    sub_elem = elems[i].getElementsByTagName('select')[0];}

    	// If not, don't do anything
    	if (typeof sub_elem == 'undefined'){
    	    continue;}

    	var id_test = sub_elem.getAttribute("id");
	//alert(id_test + " " + id_bis);
	//alert(id_bis + "\n" + id_test);
    	if (id_test != null &&
	    id_test.substring(8, 10) == id_bis.substring(8, 10) &&
    	    (elems[i].getAttribute('style') == 'display:none;' ||
	    elems[i].getAttribute('style') == 'DISPLAY: none;' ||
	    elems[i].getAttribute('style') == 'display: none;' ||
	    elems[i].getAttribute('style') == 'display:none' ||
	    elems[i].getAttribute('style') == 'DISPLAY: none' ||
	    elems[i].getAttribute('style') == 'display: none')){
    	    elems[i].removeAttribute('style');
	    continue;}

	if (id_test == id_bis){
	    var sub = id_bis.substring(8, 10);
	    sub = parseInt(sub, 10) + 1;
	    if (sub < 10){
		id_bis = id_bis.substring(0, 8) + '0' + sub + id_bis.substring(10);}
	    else{
		id_bis = id_bis.substring(0, 8) + sub + id_bis.substring(10);}
	}
    }
}


/*
 * Tooltip script
 * powered by jQuery (http://www.jquery.com)
 *
 * written by Alen Grakalic (http://cssglobe.com)
 *
 * for more info visit http://cssglobe.com/post/1695/easiest-tooltip-and-image-preview-using-jquery
 *
 */

this.tooltip = function(){
    /* CONFIG */
    // these 2 variable determine popup's distance from the cursor
    // you might want to adjust to get the right result
    xOffset = 10;
    yOffset = 20;
    /* END CONFIG */
    $("*[rel=tooltip]").hover(function(e) {
        this.t = this.title;
        this.title = "";
        $("body").append("<p id='tooltip'>"+ this.t +"</p>");
        $("#tooltip")
            .css("top",(e.pageY - xOffset) + "px")
            .css("left",(e.pageX + yOffset) + "px")
            .fadeIn("fast");
    },
    function() {
        this.title = this.t;
        $("#tooltip").remove();
    });
    $("*[rel=tooltip]").mousemove(function(e){
        $("#tooltip")
            .css("top",(e.pageY - xOffset) + "px")
            .css("left",(e.pageX + yOffset) + "px");
    });
};


$(document).ready(function(){
    tooltip();
    hide_multilines();
    $("a[rel='fancybox']").click(function() {
      $.fancybox({
        'type': 'iframe',
        'transitionIn': 'elastic',
        'transitionOut': 'elastic',
        'speedIn': 600,
        'speedOut': 200,
        'width': 670,
        'height': 400,
        'overlayColor': '#729FCF',
        'overlayOpacity': 0.8,
        'href': this.href + '?view=print',
        'onCleanup': function () {
          var fancy_iframe = $("#fancybox-frame");
          var message = fancy_iframe.find("#message .info");
          this.reload_parent_window_on_close = message ? true : false;
        },
        'onClosed': function() {
          // Reload parent if changes have been done
           if (this.reload_parent_window_on_close)
               window.location.reload();
        },
      });
      return false;
    });
});
