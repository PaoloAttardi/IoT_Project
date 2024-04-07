/* globals Chart:false, feather:false */

(function () {
  'use strict'

  feather.replace({ 'aria-hidden': 'true' })

  // Graphs
  var canvas = document.getElementById('myChart')
  var ctx = canvas.getContext('2d');

  var labels = canvas.getAttribute('data-labels').split(',');
  var valuesString = canvas.getAttribute('data-values');
  var values = JSON.parse(valuesString);
  // eslint-disable-next-line no-unused-vars
  var myChart = new Chart(canvas, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        data: values,
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
            labelString: 'Water Level'
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
  })
})()
