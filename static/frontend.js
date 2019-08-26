"use strict";

const JONES_ID1 = "Bait Locus";
const JONES_ID2 = "Prey Locus";
const DOMAIN = "https://protein-visualizer-prod.herokuapp.com/";
//const DOMAIN = "http://127.0.0.1:5000/";
const INTERACTIONS_URL = DOMAIN + "interactions";
const GENE_WORDS_URL = DOMAIN + "gene_words";
var query_type = "";
var load = 0

const INIT_STYLE = [
    // Node/Protein style
    {
        selector: "node",
        style: {
            "compound-sizing-wrt-labels": "include",
            "background-color": "#666",
            // If a protein has a commen name, use that; otherwise, use its locus.
            label: function(node) {
                if (node.data("Jones CSV") && node.data("Jones CSV")["Bait Name"]) {
                    return node.data("Jones CSV")["Bait Name"];
                } else if (
                    node.data("info") &&
                    node.data("info")["tab2"]["BIOGRID"]["Official Symbol Interactor"]
                ) {
                    return node.data("info")["tab2"]["BIOGRID"]["Official Symbol Interactor"];
                }
            },
            "font-size": 14,
            width: function(ele) {
                return 8 + 4 * Math.log2(ele.degree(true));
            },
            height: function(ele) {
                return 8 + 4 * Math.log2(ele.degree(true));
            },
            "border-width": 1,
            padding: 1,
            "background-color": function(node) {
                if (node.data("queried")) {
                    return "green";
                } else {
                    return "lightgrey";
                }
            },
            color: "white",
            opacity: 0.9,
            "text-outline-width": 2,
            "text-outline-color": "black"
        }
    },

    // Edge style
    {
        selector: "edge",
        style: {
            width: 2,
            "line-color": function(ele) {
		// If the edge is in the queried CSV AND in BioGRID
                if (ele.data("Local") != null && (ele.data("info") == "" || ele.data("info") == {} || ele.data("info") == null)) {
                    return "#ff0000";
                } else if (!ele.data("Local") && ele.data("info")) {
                    return "#808080";
                } else if (ele.data("info")) {
                    return "#009000";
                }
            },
            opacity: 0.9,
            "line-fill": function(ele) {
                if (ele.hasClass("selected-cluster")) {
                    return "linear-gradient";
                } else {
                    return "solid";
                }
            },
            "line-gradient-stop-colors": function(ele) {
                if (ele.hasClass("selected-cluster")) {
                    return (
                        ele.source().data("cluster-color") +
                        " " +
                        ele.target().data("cluster-color")
                    );
                } else {
                    return ele.style("line-color") + " " + ele.style("line-color");
                }
            }
        }
    }
]

const CYTO_INIT = {
    container: document.getElementById("cy"), // Div where we'll put the Cytoscape visualization
    style: INIT_STYLE
}

// Upon selecting a file to view locally, convert it to json and send it to Cytoscape
$("#files").change(event => {
    $("#statusdiv").text("Loading file...");

    // Get the file selected by the user
    let file = event.target.files[0];

    // Convert the CSV to .json, read elements into CY, and load the graph
    csv_to_json(file).then(json => {
        setElementsLocal(json.data);
        loadGraph();
        focused.clear();
    });
});

// Load information from Biogrid given the protein, order, and threshold parameters
$("#search_button").click(() => {
    $("#info_sidebar").hide();
    $("#edge_sidebar").hide();
    //show the parameter window
    $("#popup_window").show();
    if ($("#offcanvas-slide").is(":hidden")) {
        $("#toggle-side").click();
    }
    query_type = 'protein';
    //click search again with correct parameters
    $("#search_continue").click(() => {
	$("#exit_window").trigger("click");	
	$('#statusdiv').text('Retrieving interactions...');	
        load = 0;
        // Clear the graph first
        if (query_type == 'protein') {
            // Get user parameters
            let id = $("#protein_search").val();
            let order = $("#slider_order").val();
            let threshold = $("#slider_threshold").val();

            $("#statusdiv").text("Retrieving data from Biogrid...");

            $.ajax({
                data: JSON.stringify({
                    id: $("#protein_search").val(),
                    order: $("#slider_order").val(),
                    threshold: $("#slider_threshold").val(),
                    method: "bfs"
                }),
                url: INTERACTIONS_URL +
                    "?protein_id=" +
                    $("#protein_search").val() +
                    "&scale=" +
                    $("#slider_scale").val() +
                    "&order=" +
                    $("#slider_order").val() +
                    "&threshold=" +
                    $("#slider_threshold").val() +
                    "&organism_id=" +
                    $("#organisms").val(),
                method: "GET",
                type: "get",
                success: response => {
                    $("#statusdiv").text("Data retrieved...");
                    // Add elements to CY and load the graph
                    if (load == 0) {
                        cy.add(response.elements);
                        loadGraph();
                        load = 1;
                        query_type = '';
                    }
                },
		failure: response => {
                	$('#statusdiv').text('Something went wrong! Please reload the page and try again.');
		}
            });
        } else {}
    });
});

// Remove elements in Cytoscape if this button is clicked
$("#clear_button").click(() => {
    cy.remove(cy.elements());
    $("#statusdiv").text("Cleared the network.");
    $("#popup_window").hide();
    $("#info_sidebar").hide();
    $("#edge_sidebar").hide();
});

$("#filequery_button").click(() => {
    //document.getElementById('filequery_button').innerText = "QUERY FILE (1)";
    //parameter window pops-up
    query_type = 'file';
    $("#info_sidebar").hide();
    $("#edge_sidebar").hide();
    $("#popup_window").show();

    //displays sidebar if it is hidden
    if ($("#offcanvas-slide").is(":hidden")) {
        $("#toggle-side").click();
    }
});

//hide sidebar and exit current window displayed
$("#exit_window").click(() => {
    $("#popup_window").hide();
    $("#info_sidebar").hide();
    $("#edge_sidebar").hide();
});

// Request interactions from CSV file
$("#filequery").change(evt => {
    cy.remove(cy.elements());
    //let filename = $('#filequery'); 			//gets user selected filename, displays an alert and updates the button with the filename
    $("#statusdiv").text("QUERY FILE " + "(" + $("#filequery")[0].files[0].name + ")");
    //query_type = 'file';
    $("#search_continue").click(() => {
	$("#exit_window").trigger("click");
	$("#statusdiv").text('Retrieving interactions.');
        load = 0;
        //parameter window hides
        //$('#popup_window').hide();
        // Clear the elements first
        if (query_type == 'file') {
            cy.remove(cy.elements());
            // Convert CSV file to json, load those elements
            let file = evt.target.files[0];
            csv_to_json(file).then(json => {
                //setElementsLocal(json.data);
                console.log("requesting elements");
                console.log(json);
                // Use POST to pass in the json as an argument
                // TODO: Fix POST method; possibly just pass in CSV file (not parsed)
                return $.ajax({
                        url: INTERACTIONS_URL +
                            "?" +
                            "order=" +
                            $("#slider_order").val() +
                            "&threshold=" +
                            $("#slider_threshold").val() +
                            "&organism_id=" +
                            $("#organisms").val() +
                            "&scale=" +
                            $("#slider_scale").val() +
                            "&source_label=" +
                            "Bait Locus" +
                            "&target_label=" +
                            "Prey Locus",
                        method: "POST",
                        dataType: "json",
                        contentType: "application/json",
                        data: JSON.stringify({
                            elements: json.data
                        })
                    })
                    .done(response => {
                        if (load == 0) {
                            cy.add(response.elements);
                            loadGraph();
                            load = 1;
                            query_type = '';
                        }
                    })
                    .fail(error => {
			$('#statusdiv').text('Something went wrong! Please reload the page and try again.');
                    });
            });
        } else {}
    });
});

// cy is the core variable responsible for visualizing the data.
// We initialize cy with a default JSON stylsheet.
var cy = cytoscape(CYTO_INIT);

// Takes a CSV file and returns a *promise* containing converted JSON
// NOTE: the JSON is contaiend in response.data
var csv_to_json = csv => {
    // Using Papa for the CSV => JSON conversion
    return new Promise(function(complete, error) {
        Papa.parse(csv, {
            header: true,
            complete,
            error
        });
    });
};

// Set elements to the json provided
var setElementsLocal = json => {
    cy.remove(cy.elements());
    return addElementsLocal(json);
};

// Takes JSON extracted from CSV file; adds it to the Cytoscape div
var addElementsLocal = json => {
    $("#statusdiv").text("Parsing JSON...");

    // In case we need it, return a list of proteins found in the CSV file
    let proteins = [];

    // startBatch prevents Cytoscape from rendering elements as we add and change them
    cy.startBatch();
    for (let i = 0; i < json.length; i++) {
        let bait_name = json[i]["Bait Name"];
        let bait_locus = json[i]["Bait Locus"];
        let bait_notes = json[i]["Bait Notes"];
        let prey_locus = json[i]["Prey Locus"];
        let prey_tair = json[i]["Prey TAIR Symbols"];
        let prey_description = json[i]["Prey TAIR Description"];
        let number_interactions = json[i]["Number of Interactions"];

        if (bait_locus == "") {
            break;
        }

        // Add bait protein node
        let bait = cy.getElementById(bait_locus);
        // Add prey protein node
        let prey = cy.getElementById(prey_locus);

        // Create the bait node if it's not a duplicate
        if (bait.length == 0) {
            bait = cy.add({
                group: "nodes",
                data: {
                    id: bait_locus,
                    name: bait_locus
                }
            });
            proteins.push(bait_locus);
        }

        // Create the prey node if it's not a duplicate
        if (prey.length == 0) {
            prey = cy.add({
                group: "nodes",
                data: {
                    id: prey_locus,
                    name: prey_locus
                }
            });
            proteins.push(prey_locus);
        }

        // If bait has a name, add one
        if (bait_name) {
            bait.addClass("named");
            bait.data("name", bait_name);
        }

        // If the node doesn't already have bait notes, add it
        if (bait_notes) {
            bait.data("bait_notes", bait_notes);
        }

        // If the node doesn't have prey_tair, add it
        if (prey_tair) {
            prey.data("prey_tair", prey_tair);
        }

        // If the node doesn't have prey_description, add it
        if (prey_description) {
            prey.data("prey_description", prey_description);
        }

        // Add edge; ignore duplicates
        let edge_id = bait_locus + "_" + prey_locus;
        if (cy.getElementById(edge_id).length == 0) {
            cy.add({
                group: "edges",
                data: {
                    id: edge_id,
                    source: bait_locus,
                    target: prey_locus,
                    number_interactions: number_interactions
                }
            });
        } else {
            $("#status").text("duplicate entry: " + edge_id);
        }
    }

    // In case we need it, return an array of proteins found in the CSV file
    proteins.sort();
    return proteins;
};

// Once we have elements, load / display the graph
var loadGraph = () => {
    $("#statusdiv").text("Loading Graph...");

    // 'Cose': a particular built-in layout (for positioning nodes)
    var layout = cy.layout({
        name: "cose",
        nodeDimensionsIncludeLabels: true,
        padding: 1000,
        nodeRepulsion: function(node) {
            return 100000;
        },
        nodeOverlap: 4
    });
    layout.promiseOn("layoutstop").then(thing => {
        setTimeout(function() {
            focused.clear();
        }, 1);
    });
    layout.run();

    cy.style().fromJson(INIT_STYLE).update();
    if ($("#offcanvas-slide").is(":visible")) {
        $("#toggle-side").click();
    }
    $("#statusdiv").text("");
};

// Add event listener for keys
window.addEventListener("keydown", keypress, false);

function keypress(e) {
    // Cmd + Z
    if (e.key == "z" && e.metaKey) {
        focused.back();

        // Spacebar
    } else if (e.key == " ") {
        focused.clear();
    }
}

let get_keywords = (elements) => {
	let id_list = [];
	elements.nodes().each(node => {
		if (node.data("info")) {
			id_list.push(node.data("info")["tab2"]["BIOGRID"]["Entrez Gene Interactor"]);
		}
	});	

    // NOTE: This is where we put our list of gene words that we want to ignore. 
				// TODO: Let the user specify words they'd like to ignore.
    let filter_list = ['protein', 'proteins', 'gene', 'genes'];
    return $.ajax({
        url: GENE_WORDS_URL,
	traditional: true,
	data: {
		id_list: id_list,
		filter_list: filter_list
	},
        method: "GET",
        type: "get",
    });
};

cy.on("click", "node", function(evt) {
    let node = evt.target;
    let clicks = evt.originalEvent.detail;
    if (evt.originalEvent.shiftKey) {			// shift + click
        focused.shiftclick(node, clicks + 1);
    } else if (evt.originalEvent.altKey){		// alt + click
        focused.altclick(node, clicks + 1);
    }
    else if (evt.originalEvent.metaKey) {		// cmd + click
		focused.click(node, clicks + 1);
    }
    else {										// simple click 
        print_node_info(node);
    }
});


cy.on('click', 'edge', function(evt) {
    let edge = evt.target;
    let clicks = evt.originalEvent.detail;
    let elements = edge.union(edge.target()).union(edge.source());

    if (evt.originalEvent.shiftKey) {			// shift + click
        focused.shiftclick(elements, clicks);
    }
    else if (evt.originalEvent.metaKey) {		// cmd + click
        focused.click(elements, clicks);
    }
    else {										// simple click
        print_edge_info(edge);
    }
});

let print_edge_info = (edge) => {
    if ($("#offcanvas-slide").is(":hidden")) {
        $("#toggle-side").click();
    }
    $("#info_sidebar").hide();
    $("#popup_window").hide();

    $("#edge_sidebar").show();

    //clear all info windows
    $("#edgeinfoA").text("");
    $("#edgeinfoB").text("");
    $("#cluster_key_info_edge_A").text("");
    $("#cluster_key_info_edge_B").text("");
    $("#list_neighbors_edge_A").text("");
    $("#list_neighbors_edge_B").text("");
    $("#experimental_info_interaction").text("");
    $("#edge_links").text("");

    let nodeA = edge.source();
    let nodeB = edge.target();
    var collection = cy.collection();

    let key = Object.keys(edge.data("info")["tab2"])[0];
    let edge_info_path = edge.data("info")["tab2"][key];
    let synonyms_A = edge_info_path["Synonyms Interactor A"];
    let synonyms_B = edge_info_path["Synonyms Interactor B"];

    $("#edge_titleA").text("Protein A: " + edge.source().style("label"));
    $("#edge_titleB").text("Protein B: " + edge.target().style("label"));
    $("#ClusterA").text(edge.source().style("label") + " Neighboring Proteins:");
    $("#ClusterB").text(edge.target().style("label") + " Neighboring Proteins:");
    $("#KeywordsA").text(edge.source().style("label") + " Neighboring Protein Keywords:");
    $("#KeywordsB").text(edge.target().style("label") + " Neighboring Protein Keywords:");
    //add edge information node A and node B
    $("#edgeinfoA").append(
        "<b>Official Symbol Interactor: </b>" + 
        String(edge_info_path["Official Symbol Interactor A"]) +
        "</br>"
    );
    $("#edgeinfoA").append(
        "<b>Synonyms Interactor: </b>" + synonyms_A.replace(/\|/g, " , ") + "</br>"
    );
    $("#edgeinfoA").append(
        "<b>Systematic Name Interactor: </b>" +
        edge_info_path["Systematic Name Interactor B"] +
        "</br>"
    );

    $("#edgeinfoB").append(
        "<b>Official Symbol Interactor: </b>" +
        edge_info_path["Official Symbol Interactor B"] +
        "</br>"
    );
    $("#edgeinfoB").append(
        "<b>Synonyms Interactor: </b>" + synonyms_B.replace(/\|/g, " , ") + "</br>"
    );
    $("#edgeinfoB").append(
        "<b>Systematic Name Interactor: </b>" +
        edge_info_path["Systematic Name Interactor B"] +
        "</br>"
    );

    //cluster keywords for both nodes in question
    get_keywords(edge.source().neighborhood().union(edge.source())).then((response) => {
            $('#list_neighbors_edge_A').text((response.slice(0, 20).join(', ')));
    });

    get_keywords(edge.target().neighborhood().union(edge.target())).then((response) => {
            $('#list_neighbors_edge_B').text((response.slice(0, 20).join(', ')));
    });		

    //defining cluster members for A and B
    edge
        .source()
        .neighborhood()
        .nodes()
        .each(node => {
            $("#list_neighbors_edge_A").append(node.style("label") + "</br>");
        });

    edge
        .target()
        .neighborhood()
        .nodes()
        .each(node => {
            $("#list_neighbors_edge_B").append(node.style("label") + "</br>");
        });

    //experimental info added
    console.log(edge._private.data["experimental"]);
    let edge_experimental_method = Object.values(
        edge._private.data["experimental"]
    )[0];
    $("#experimental_info_interaction").append(
        JSON.stringify(Object.keys(edge_experimental_method)[0]).replace(
            /['"]+/g,
            ""
        )
    );

    //edge links for A and B
    $("#edge_links").append(
        '<a href="https://www.ncbi.nlm.nih.gov/gene/' +
        edge_info_path["Entrez Gene Interactor A"] +
        '" target="_blank">Entrez Gene Interactor A</a></br>'
    );
    $("#edge_links").append(
        '<a href="https://thebiogrid.org/' +
        edge_info_path["BioGRID ID Interactor A"] +
        '" target="_blank">BioGRID Interactor A</a></br></br>'
    );

    $("#edge_links").append(
        '<a href="https://www.ncbi.nlm.nih.gov/gene/' +
        edge_info_path["Entrez Gene Interactor B"] +
        '" target="_blank">Entrez Gene Interactor B</a></br>'
    );
    $("#edge_links").append(
        '<a href="https://thebiogrid.org/' +
        edge_info_path["BioGRID ID Interactor B"] +
        '" target="_blank">BioGRID Interactor B</a></br></br>'
    );
    $("#edge_links").append(
        '<a href="https://www.ncbi.nlm.nih.gov/pubmed/' +
        edge_info_path["Pubmed ID"] +
        '" target="_blank">Pubmed ID</a></br></br>'
    );
};

// Print protein information
var print_node_info = node => {		
    $("#edge_sidebar").hide();
    $("#popup_window").hide();
    $("#info_sidebar").show();
    if ($("#offcanvas-slide").is(":hidden")) {
        $("#toggle-side").click();
    }

    $("#info_title").text("");
    $("#nodeinfo").text("");
    $("#list_neighbors").text("");
    $("#node_links").text("");
   
    $("#info_title").prepend(node.style("label") + " Information");
    $("#nodeinfo").append(
        "Official Symbol Interactor: " + node.style('label') + "</br>"
    );

    // List of neighboring nodes
    get_keywords(node.neighborhood().union(node)).then((response) => { 
	    $('#cluster_key_info').text((response.slice(0, 20).join(', ')));
	});
    node.neighborhood().nodes().each(node => {
            $("#list_neighbors").append(node.style("label") + "</br>");
        });

    let infopath_json, synonyms;
    if (!node._private.data.info){
	return;    
    }else if (node._private.data.info.tab2){
	    infopath_json = node._private.data.info.tab2.BIOGRID; // where our protein data is stored
	    synonyms = infopath_json["Synonyms Interactor"];
    } else {
	    infopath_json = {};
	    synonyms = "";
    }

    $("#nodeinfo").append(
        "Synonyms Interactor: " + synonyms.replace(/\|/g, " , ") + "</br>"
    );
    $("#nodeinfo").append(
        "Systematic Name Interactor: " +
        infopath_json["Systematic Name Interactor"] +
        "</br>"
    );

    $("#node_links").append(
        '<a href="https://www.ncbi.nlm.nih.gov/gene/' +
        node._private.data.info.tab2.BIOGRID["Entrez Gene Interactor"] +
        '" target="_blank">Entrez Gene Interactor</a></br>'
    );
    $("#node_links").append(
        '<a href="https://thebiogrid.org/' +
        node._private.data.info.tab2.BIOGRID["BioGRID ID Interactor"] +
        '" target="_blank">BioGRID ID Interactor</a></br>'
    );
};

// focusedElements: Provides functionality for setting specific nodes "in focus"
// Keeps a stack of views for the user to easily revert back
class elementTracker {
    // Initialize the starting elements to be focused/selected
    constructor(elements) {
        // Keep a stack to maintain state

        this.elementStack = [];
        this.stackSize = 0;
        if (elements) {
            this.select(elements, true);
        }
    }

    // Focus on the selected elements and hide everything else
    viewSelected() {
		get_keywords(this.elements).then((response) => {
				console.log(response)}
		);	

        if (this.stackSize > 0) {
            cy.animate({
                fit: {
                    eles: this.elements
                },
                duration: 350
            });
        }

        this.elements.animate({
            style: {
                opacity: 0.9
            },
            duration: 350
        });

        this.elements.complement().animate({
            style: {
                opacity: 0.07
            },
            duration: 350
        });
    }

    // Add the new list of selected elements to the call stack; focus on these elements
    select(elements, hidebackground) {
        this.elementStack[this.stackSize] = elements;
        this.stackSize++;
        this.viewSelected(hidebackground);
    }

    // Add elements to the set of already focused/selected elements
    addElements(elements) {
        this.select(this.elements.union(elements), false);
    }

    // Remove these elements from the set of already selcted elements
    subtractElements(elements) {
        // This includes nodes that we want to retain
        let subtracted = this.elements.difference(elements);

        // Filter elements by edges
        let retainedEdges = subtracted.filter(element => {
            return element.isEdge();
        });

        retainedEdges.forEach(edge => {
            subtracted = subtracted.union(edge.target());
            subtracted = subtracted.union(edge.source());
        });

        this.select(subtracted, false);
    }

    // Get top of selected element stack
    get elements() {
        return this.elementStack[this.stackSize - 1];
    }

    // Zoom in on the entire graph
    clear() {
        this.select(cy.elements(), true);	
	 $("#exit_window").trigger("click");
    }

    // Equivalent of undo: revert to the previous selection of protein (if it exists)
    // TODO: Fix bug when stack size is 0 or 1
    back() {
        if (this.stackSize == 0) {
            return;
        } else {
            this.stackSize--;
            this.viewSelected(true);
        }
    }

    // Find every element within n connections of the specified elements
    getNeighborhood(elements, n) {
        if (n == 1) {
            return elements
                .nodes()
                .edgesWith(elements.nodes())
                .union(elements.nodes());
        } else {
            return this.getNeighborhood(
                elements.union(elements.neighborhood()),
                n - 1
            );
        }
    }

    // Number of nodes connected to this node that are in focus
    focusedDegree(node, newelements) {
        let edges = node.edges(edge => {
            return newelements.contains(edge);
        });

        let size = edges.size();
    }

    click(elements, n) {
        this.select(this.getNeighborhood(elements, n), false);
    }

    shiftclick(elements, n) {
        elements = this.getNeighborhood(elements, n);
        this.addElements(elements);
    }

    altclick(elements, n) {
        this.subtractElements(this.getNeighborhood(elements, n));
    }

    ctrlclick(elements) {
        elements = this.getNeighborhood(elements, n);
        this.addElements(elements);
    }
}

var focused = new elementTracker();

// Use this to track element views
//var focused = new elementTracker();

// Generate a random color
var randomColor = function() {
    //random 2-digit numbers between 0 and 255
    let r = ((1 << 8) * Math.random()) | 0;
    let g = ((1 << 8) * Math.random()) | 0;
    let b = ((1 << 8) * Math.random()) | 0;

    // We pick a number between 0 and 255 to bias the brightness
    let ratio = 181 / Math.max(r, g, b);
    r *= ratio;
    g *= ratio;
    b *= ratio;
    return makeColor(r, g, b);
};

// Takes three integers from 0 to 255 as inputs; returns a formatted string representing the corresponding color
var makeColor = function(r, g, b) {
    r = Math.round(r).toString(16);
    g = Math.round(g).toString(16);
    b = Math.round(b).toString(16);

    if (r.length == 1) {
        r = "0" + r;
    }
    if (g.length == 1) {
        g = "0" + g;
    }
    if (b.length == 1) {
        b = "0" + b;
    }
    return "#" + r + g + b;
};

var order_slider = document.getElementById("slider_order");
var order_out = document.getElementById("slider_value_order");
order_out.innerHTML = order_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
order_slider.oninput = function() {
    order_out.innerHTML = this.value;
};

var thresh_slider = document.getElementById("slider_threshold");
var thresh_out = document.getElementById("slider_value_threshold");
thresh_out.innerHTML = thresh_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
thresh_slider.oninput = function() {
    thresh_out.innerHTML = this.value;
};

var scale_slider = document.getElementById("slider_scale");
var scale_out = document.getElementById("slider_value_scale");
scale_out.innerHTML = scale_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
scale_slider.oninput = function() {
    scale_out.innerHTML = this.value;
};

var acl_slider = document.getElementById("slider_ACL");
var acl_out = document.getElementById("slider_value_ACL");
acl_out.innerHTML = acl_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
acl_slider.oninput = function() {
    acl_out.innerHTML = this.value;
};

var acm_slider = document.getElementById("slider_ACM");
var acm_out = document.getElementById("slider_value_ACM");
acm_out.innerHTML = acm_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
acm_slider.oninput = function() {
    acm_out.innerHTML = this.value;
};

var acr_slider = document.getElementById("slider_ACR");
var acr_out = document.getElementById("slider_value_ACR");
acr_out.innerHTML = acr_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
acr_slider.oninput = function() {
    acr_out.innerHTML = this.value;
};

var acw_slider = document.getElementById("slider_ACW");
var acw_out = document.getElementById("slider_value_ACW");
acw_out.innerHTML = acw_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
acw_slider.oninput = function() {
    acw_out.innerHTML = this.value;
};

var ba_slider = document.getElementById("slider_BA");
var ba_out = document.getElementById("slider_value_BA");
ba_out.innerHTML = ba_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
ba_slider.oninput = function() {
    ba_out.innerHTML = this.value;
};

var ccs_slider = document.getElementById("slider_CCS");
var ccs_out = document.getElementById("slider_value_CCS");
ccs_out.innerHTML = ccs_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
ccs_slider.oninput = function() {
    ccs_out.innerHTML = this.value;
};

var cf_slider = document.getElementById("slider_CF");
var cf_out = document.getElementById("slider_value_CF");
cf_out.innerHTML = cf_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
cf_slider.oninput = function() {
    cf_out.innerHTML = this.value;
};

var cl_slider = document.getElementById("slider_CL");
var cl_out = document.getElementById("slider_value_CL");
cl_out.innerHTML = cl_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
cl_slider.oninput = function() {
    cl_out.innerHTML = this.value;
};

var cp_slider = document.getElementById("slider_CP");
var cp_out = document.getElementById("slider_value_CP");
cp_out.innerHTML = cp_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
cp_slider.oninput = function() {
    cp_out.innerHTML = this.value;
};

var fw_slider = document.getElementById("slider_FW");
var fw_out = document.getElementById("slider_value_FW");
fw_out.innerHTML = fw_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
fw_slider.oninput = function() {
    fw_out.innerHTML = this.value;
};

var fret_slider = document.getElementById("slider_FRET");
var fret_out = document.getElementById("slider_value_FRET");
fret_out.innerHTML = fret_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
fret_slider.oninput = function() {
    fret_out.innerHTML = this.value;
};

var pca_slider = document.getElementById("slider_PCA");
var pca_out = document.getElementById("slider_value_PCA");
pca_out.innerHTML = pca_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
pca_slider.oninput = function() {
    pca_out.innerHTML = this.value;
};

var pp_slider = document.getElementById("slider_PP");
var pp_out = document.getElementById("slider_value_PP");
pp_out.innerHTML = pp_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
pp_slider.oninput = function() {
    pp_out.innerHTML = this.value;
};

var pr_slider = document.getElementById("slider_PR");
var pr_out = document.getElementById("slider_value_PR");
pr_out.innerHTML = pr_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
pr_slider.oninput = function() {
    pr_out.innerHTML = this.value;
};

var plm_slider = document.getElementById("slider_PLM");
var plm_out = document.getElementById("slider_value_PLM");
plm_out.innerHTML = plm_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
plm_slider.oninput = function() {
    plm_out.innerHTML = this.value;
};

var rc_slider = document.getElementById("slider_RC");
var rc_out = document.getElementById("slider_value_RC");
rc_out.innerHTML = rc_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
rc_slider.oninput = function() {
    rc_out.innerHTML = this.value;
};

var th_slider = document.getElementById("slider_TH");
var th_out = document.getElementById("slider_value_TH");
th_out.innerHTML = th_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
th_slider.oninput = function() {
    th_out.innerHTML = this.value;
};

var dgd_slider = document.getElementById("slider_DGD");
var dgd_out = document.getElementById("slider_value_DGD");
dgd_out.innerHTML = dgd_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
dgd_slider.oninput = function() {
    dgd_out.innerHTML = this.value;
};

var dl_slider = document.getElementById("slider_DL");
var dl_out = document.getElementById("slider_value_DL");
dl_out.innerHTML = dl_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
dl_slider.oninput = function() {
    dl_out.innerHTML = this.value;
};

var dr_slider = document.getElementById("slider_DR");
var dr_out = document.getElementById("slider_value_DR");
dr_out.innerHTML = dr_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
dr_slider.oninput = function() {
    dr_out.innerHTML = this.value;
};

var ng_slider = document.getElementById("slider_NG");
var ng_out = document.getElementById("slider_value_NG");
ng_out.innerHTML = ng_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
ng_slider.oninput = function() {
    ng_out.innerHTML = this.value;
};

var pe_slider = document.getElementById("slider_PE");
var pe_out = document.getElementById("slider_value_PE");
pe_out.innerHTML = pe_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
pe_slider.oninput = function() {
    pe_out.innerHTML = this.value;
};

var ps_slider = document.getElementById("slider_PS");
var ps_out = document.getElementById("slider_value_PS");
ps_out.innerHTML = ps_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
ps_slider.oninput = function() {
    ps_out.innerHTML = this.value;
};

var pg_slider = document.getElementById("slider_PG");
var pg_out = document.getElementById("slider_value_PG");
pg_out.innerHTML = pg_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
pg_slider.oninput = function() {
    pg_out.innerHTML = this.value;
};

var sgd_slider = document.getElementById("slider_SGD");
var sgd_out = document.getElementById("slider_value_SGD");
sgd_out.innerHTML = sgd_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
sgd_slider.oninput = function() {
    sgd_out.innerHTML = this.value;
};

var sh_slider = document.getElementById("slider_SH");
var sh_out = document.getElementById("slider_value_SH");
sh_out.innerHTML = sh_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
sh_slider.oninput = function() {
    sh_out.innerHTML = this.value;
};

var sl_slider = document.getElementById("slider_SL");
var sl_out = document.getElementById("slider_value_SL");
sl_out.innerHTML = sl_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
sl_slider.oninput = function() {
    sl_out.innerHTML = this.value;
};

var sr_slider = document.getElementById("slider_SR");
var sr_out = document.getElementById("slider_value_SR");
sr_out.innerHTML = sr_slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
sr_slider.oninput = function() {
    sr_out.innerHTML = this.value;
};

//display instructions for user
$("#information").click(() => {
    $("#view").hide();
    $("#information_display").show();

    $("#information_back").click(() => {
        $("#view").show();
        $("#information_display").hide();
    });
});

//hide/show edges that loop to the same protein
$("#toggle_loops").click(() => {
    cy.edges().each(edge => {
        let src = edge.source();
        let dst = edge.target();
        if (src == dst) {
            if (edge.is(":hidden")) {
                edge.show();
            } else {
                edge.hide();
            }
        }
    });
});

//hide/show elements that were not queried on (works for file query)
$("#toggle_non_queried").click(() => {
    cy.nodes().each(node => {
        if (node._private.data.Local == null) {
            if (node.is(":hidden")) {
                node.show();
            } else {
                node.hide();
            }
        }
    });
});

$("#toggle_deg_one").click(() => {
    cy.nodes().each(node => {
        if (node.degree(false) == 1) {
            if (node.is(":hidden")) {
                node.show();
            } else {
                node.hide();
            }
        }
    });
});

$("#methods_button").click(() => {
    if ($("#exp_method_weight_sliders").is(":hidden")) {
        $("#exp_method_weight_sliders").show();
    } else {
        $("#exp_method_weight_sliders").hide();
    }
});
