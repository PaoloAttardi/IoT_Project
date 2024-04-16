(function () {
  'use strict'

  feather.replace({ 'aria-hidden': 'true' })

  // Graphs
  // First Canvas
  var canvas1 = document.getElementById('tankChart');
  var ctx1 = canvas1.getContext('2d');

  var labels1 = [];
  var valuesString1 = canvas1.getAttribute('data-values');
  var values1 = JSON.parse(valuesString1);
  for (var i = 0; i < values1.length; i++) {
    labels1.push(i);
  }
  var myChart1 = new Chart(canvas1, {
    type: 'line',
    data: {
      labels: labels1,
      datasets: [{
        data: values1,
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#007bff',
        borderWidth: 4,
        pointBackgroundColor: '#007bff'
      }]
    },
    options: {
      scales: {
        yAxes: [{
          scaleLabel: {
            display: true,
            labelString: 'Tank Level'
          },
          ticks: {
            beginAtZero: true
          }
        }]
      },
      legend: {
        display: false
      }
    }
  });

  // Second Canvas
  var canvas2 = document.getElementById('bowlChart');
  var ctx2 = canvas2.getContext('2d');

  var labels2 = [];
  var valuesString2 = canvas2.getAttribute('data-values');
  var values2 = JSON.parse(valuesString2);
  for (var j = 0; j < values2.length; j++) {
    labels2.push(j);
  }
  var myChart2 = new Chart(canvas2, {
    type: 'line',
    data: {
      labels: labels2,
      datasets: [{
        data: values2,
        lineTension: 0,
        backgroundColor: 'transparent',
        borderColor: '#ff0000', // Change color for differentiation
        borderWidth: 4,
        pointBackgroundColor: '#ff0000' // Change color for differentiation
      }]
    },
    options: {
      scales: {
        yAxes: [{
          scaleLabel: {
            display: true,
            labelString: 'Bowl Level'
          },
          ticks: {
            beginAtZero: true
          }
        }]
      },
      legend: {
        display: false
      }
    }
  });
})();
