function csv_to_json(file, complete) {
  return Papa.parse(file, {
    header: true,
    complete
  });
}

function setStatus(status) {
  $("#status").html(status);
}

$("#filequery").change(evt => {
  cy.remove(cy.elements());
  let csv_file = evt.target.files[0];
  var threshold = $("#threshold").val();
  var order = $("#order").val();
  setStatus("This might take a bit...");
  csv_to_json(csv_file, function(json) {
    $.ajax({
      url: "http://127.0.0.1:5000/interactions",
      method: "POST",
      dataType: "json",
      contentType: "application/json",
      data: JSON.stringify({
        elements: json.data,
        order: order,
        threshold: threshold
      })
    }).done(response => {
      cy.add(response.elements);
      cy.layout({ name: "cose" }).run();
      setStatus("All done!");
    });
  });
});

var cy = cytoscape({
  container: document.getElementById("cy"),
  style: [
    {
      selector: "node",
      style: {
        "compound-sizing-wrt-labels": "include",
        "background-color": "#666",
        label: function(node) {
          if (node.data("Jones CSV") && node.data("Jones CSV")["Bait Name"]) {
            return node.data("Jones CSV")["Bait Name"];
          } else if (
            node.data("info") &&
            node.data("info")["tab2"]["BIOGRID"]["Official Symbol Interactor"]
          ) {
            return node.data("info")["tab2"]["BIOGRID"][
              "Official Symbol Interactor"
            ];
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
    {
      selector: "edge",
      style: {
        width: 2,
        "line-color": function(ele) {
          if (ele.hasClass("selected-cluster")) {
          } else if (
            ele.data("Jones CSV") != null &&
            ele.data("info") == null
          ) {
            return "red";
          } else if (!ele.data("Jones CSV") && ele.data("info")) {
            return "lightgrey";
          } else if (ele.data("info")) {
            return "lightgreen";
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
});
