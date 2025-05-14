// File: D:\.Origen\Dash_\static\assets\js\chart\chart.js

function fetchDataAndCreateChart() {
  fetch('/obtener_datos_grafica/')
      .then(response => response.json())
      .then(data => {
          console.log("Datos recibidos (detallados):", JSON.stringify(data, null, 2));
          if (data.length === 0) {
              console.warn("No se recibieron datos del servidor");
          }
          createChart(data);
      })
      .catch(error => console.error('Error:', error));
}

function createChart(data) {
  am5.ready(function() {
      console.log("Creando el gráfico con los datos:", data);
      // Create root element
      var root = am5.Root.new("chartdiv");
      
      // Set themes
      root.setThemes([am5themes_Animated.new(root)]);
      
      root.dateFormatter.setAll({
          dateFormat: "yyyy-MM-dd",
          dateFields: ["valueX"]
      });
      
      // Create chart
      var chart = root.container.children.push(
          am5xy.XYChart.new(root, {
              panX: true,
              panY: true,
              wheelX: "panX",
              wheelY: "zoomX",
              pinchZoomX: true,
              layout: root.verticalLayout
          })
      );
      
      // Add cursor
      var cursor = chart.set("cursor", am5xy.XYCursor.new(root, {
          behavior: "none"
      }));
      cursor.lineY.set("visible", false);
      
      // Create axes
      var xAxis = chart.xAxes.push(
        am5xy.DateAxis.new(root, {
          maxDeviation: 0.2,
          baseInterval: { timeUnit: "day", count: 1 },
          renderer: am5xy.AxisRendererX.new(root, {
            minGridDistance: 50,
            cellStartLocation: 0.1,
            cellEndLocation: 0.9
          }),
          tooltip: am5.Tooltip.new(root, {}),
          tooltipDateFormat: "yyyy-MM-dd"
        })
      );
      
      var yAxis0 = chart.yAxes.push(
          am5xy.ValueAxis.new(root, {
              renderer: am5xy.AxisRendererY.new(root, {
                  pan: "zoom"
              })
          })
      );
      
      var yRenderer1 = am5xy.AxisRendererY.new(root, {
          opposite: true
      });
      yRenderer1.grid.template.set("forceHidden", true);
      
      var yAxis1 = chart.yAxes.push(
          am5xy.ValueAxis.new(root, {
              renderer: yRenderer1,
              syncWithAxis: yAxis0
          })
      );
      
      // Ajustar el rango de fechas si hay pocos datos
      if (data.length > 0) {
      var firstDate = new Date(data[0].date);
      var lastDate = new Date(data[data.length - 1].date);

      var endOfRange = new Date(lastDate.getFullYear(), lastDate.getMonth(), 15);
      if (lastDate < endOfRange) {
          lastDate = endOfRange;
        }

  
        // Si hay menos de 15 días de datos, extender el rango
        if ((lastDate - firstDate) / (1000 * 60 * 60 * 24) < 15) {
          lastDate = new Date(firstDate.getFullYear(), firstDate.getMonth(), 15);
        }
          
          if ((lastDate - firstDate) / (1000 * 60 * 60 * 24) < 7) {
              lastDate = new Date(firstDate.getTime() + (7 * 24 * 60 * 60 * 1000));
          }
          
          xAxis.set("min", firstDate.getTime());
          xAxis.set("max", lastDate.getTime());
      }
      
      // Add series
      var columnSeries1 = chart.series.push(
        am5xy.ColumnSeries.new(root, {
          name: "Ventas Canceladas",
          xAxis: xAxis,
          yAxis: yAxis0,
          valueYField: "market1",
          valueXField: "date",
          clustered: false,
          tooltip: am5.Tooltip.new(root, {
            pointerOrientation: "horizontal",
            labelText: "{name}: {valueY}"
          })
        })
      );
      
      columnSeries1.columns.template.setAll({
        width: am5.percent(60),
        fillOpacity: 0.8,
        strokeOpacity: 0,
        fill: am5.color(0xB4E6FD),  // Light blue color for Ventas Canceladas
        stroke: am5.color(0xB4E6FD)
      });
      
      var columnSeries0 = chart.series.push(
        am5xy.ColumnSeries.new(root, {
          name: "Ventas Positivas",
          xAxis: xAxis,
          yAxis: yAxis0,
          valueYField: "sales0",
          valueXField: "date",
          clustered: false,
          tooltip: am5.Tooltip.new(root, {
            pointerOrientation: "horizontal",
            labelText: "{name}: {valueY}"
          })
        })
      );
      
      columnSeries0.columns.template.setAll({
        width: am5.percent(40),
        fillOpacity: 0.8,
        strokeOpacity: 0,
        fill: am5.color(0x6BA5DB),  // Darker blue color for Ventas Positivas
        stroke: am5.color(0x6BA5DB)
      });
      
      var series0 = chart.series.push(
        am5xy.SmoothedXLineSeries.new(root, {
          name: "% Ventas positivas",
          xAxis: xAxis,
          yAxis: yAxis1,
          valueYField: "market0",
          valueXField: "date",
          tooltip: am5.Tooltip.new(root, {
            pointerOrientation: "horizontal",
            labelText: "{name}: {valueY}%"
          })
        })
      );
      
      series0.strokes.template.setAll({
        strokeWidth: 2,
        stroke: am5.color(0x00FF00),
        strokeDasharray: [2, 2]
      });
      
      // Add bullet
      series0.bullets.push(function () {
          return am5.Bullet.new(root, {
              sprite: am5.Circle.new(root, {
                  stroke: series0.get("stroke"),
                  strokeWidth: 2,
                  fill: am5.color(0xffffff),
                  radius: 4
              })
          });
      });
      
      var series1 = chart.series.push(
        am5xy.SmoothedXLineSeries.new(root, {
          name: "Estadística General",
          xAxis: xAxis,
          yAxis: yAxis1,
          valueYField: "sales1",
          valueXField: "date",
          tooltip: am5.Tooltip.new(root, {
            pointerOrientation: "horizontal",
            labelText: "{name}: {valueY}"
          })
        })
      );
      
      series1.strokes.template.setAll({
        strokeWidth: 2,
        stroke: am5.color(0x9747FF)  // Purple color for Estadística General line
      });
      
      // Add bullet
      series1.bullets.push(function () {
          return am5.Bullet.new(root, {
              sprite: am5.Circle.new(root, {
                  stroke: series1.get("stroke"),
                  strokeWidth: 2,
                  fill: am5.color(0xffffff),
                  radius: 4
              })
          });
      });
      
      // Add scrollbar
      var scrollbar = chart.set("scrollbarX", am5xy.XYChartScrollbar.new(root, {
          orientation: "horizontal",
          height: 60
      }));
      
      var sbDateAxis = scrollbar.chart.xAxes.push(
          am5xy.DateAxis.new(root, {
              baseInterval: { timeUnit: "day", count: 1 },
              renderer: am5xy.AxisRendererX.new(root, {})
          })
      );
      
      var sbValueAxis0 = scrollbar.chart.yAxes.push(
          am5xy.ValueAxis.new(root, {
              renderer: am5xy.AxisRendererY.new(root, {})
          })
      );
      
      var sbValueAxis1 = scrollbar.chart.yAxes.push(
          am5xy.ValueAxis.new(root, {
              renderer: am5xy.AxisRendererY.new(root, {})
          })
      );
      
      var sbSeries0 = scrollbar.chart.series.push(
          am5xy.ColumnSeries.new(root, {
              valueYField: "sales0",
              valueXField: "date",
              xAxis: sbDateAxis,
              yAxis: sbValueAxis0
          })
      );
      
      sbSeries0.columns.template.setAll({ fillOpacity: 0.5, strokeOpacity: 0 });
      
      var sbSeries1 = scrollbar.chart.series.push(
          am5xy.LineSeries.new(root, {
              valueYField: "market0",
              valueXField: "date",
              xAxis: sbDateAxis,
              yAxis: sbValueAxis1
          })
      );
      
      var legend = chart.children.push(
          am5.Legend.new(root, {
              centerX: am5.percent(50),
              x: am5.percent(50),
              layout: root.horizontalLayout
          })
      );
      legend.data.setAll(chart.series.values);
      
      // Procesar los datos
      data.forEach(function(item) {
        // Asumiendo que item.date está en formato "YYYY-MM-DD"
        var parts = item.date.split('-');
        item.date = new Date(parts[0], parts[1] - 1, parts[2]).getTime();
    });
      
      // Set data
      console.log("Datos para columnSeries1:", data);
      columnSeries1.data.setAll(data);
      console.log("Datos para columnSeries0:", data);
      columnSeries0.data.setAll(data);
      console.log("Datos para series0:", data);
      series0.data.setAll(data);
      console.log("Datos para series1:", data);
      series1.data.setAll(data);
      sbSeries0.data.setAll(data);
      sbSeries1.data.setAll(data);
      
      // Make stuff animate on load
      chart.series.each(function(series) {
          series.appear(1000, 100);
      });

      // Forzar una actualización del gráfico
      chart.series.each(function(series) {
          series.dataItems.forEach(function(dataItem) {
              dataItem.set("visible", false);
              dataItem.set("visible", true);
          });
      });

      chart.appear(1000, 100);
  });
}

// Llamar a la función para obtener datos y crear el gráfico
fetchDataAndCreateChart();