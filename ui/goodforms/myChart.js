function createData()
{
    var finished = 0;
    var pending = 0;
    var empty = 0;
    var notregistered = 0;

    var browse_list = document.getElementById("browse-list");
    var trs = browse_list.getElementsByTagName("tr");
    for (var i = 1; i < trs.length; i++) {
	var td_value = trs[i].getElementsByTagName("td")[1].getElementsByTagName("span")[0].innerHTML;
	if (td_value == "Finished") {
	    finished += 1;
	}
	if (td_value == "Pending") {
	    pending += 1;
	}
	if (td_value == "Empty") {
	    empty += 1;
	}
	if (td_value == "Not Registered") {
	    notregistered += 1;
	}
    }
    var data = [
	{
	    value : finished,
	    color: "#00ff00"
	},
	{
	    value : pending,
	    color: "#ffcc00"
	},
	{
	    value : empty,
	    color: "#ff0000"
	},
	{
	    value: notregistered,
	    color: "#555555"
	}
    ];
    return data;
}
