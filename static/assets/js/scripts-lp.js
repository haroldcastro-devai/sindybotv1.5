function toggleRows(element) {
element.classList.toggle('active');
const date = element.getAttribute('data-date');
const childRows = document.querySelectorAll(`tr.child-row[data-parent="${date}"]`);
childRows.forEach(row => {
  row.classList.toggle('active');
});
}

function descargarRegistros(fecha, event) {
event.stopPropagation(); // Evita que se active el toggle al hacer clic en el botón de descarga
window.location.href = `/descargar-registros-fecha/${fecha}/`;
}

function actualizarTabla() {
$.ajax({
  url: window.location.href,
  success: function(data) {
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = data;

      // Actualizar tabla de ventas
      const newSalesTableBody = tempDiv.querySelector('#salesTableBody');
      const expandedSalesDates = Array.from(document.querySelectorAll('#salesTableBody .date-row.active'))
          .map(row => row.getAttribute('data-date'));

      if (newSalesTableBody) {
          document.querySelector('#salesTableBody').innerHTML = newSalesTableBody.innerHTML;
          expandedSalesDates.forEach(date => {
              const dateRow = document.querySelector(`#salesTableBody tr.date-row[data-date="${date}"]`);
              if (dateRow) toggleRows(dateRow);
          });
      }

      // Actualizar tabla de feedback
      const newFeedbackTableBody = tempDiv.querySelector('#feedbackTableBody');
      const expandedFeedbackDates = Array.from(document.querySelectorAll('#feedbackTableBody .date-row.active'))
          .map(row => row.getAttribute('data-date'));

      if (newFeedbackTableBody) {
          document.querySelector('#feedbackTableBody').innerHTML = newFeedbackTableBody.innerHTML;
          expandedFeedbackDates.forEach(date => {
              const dateRow = document.querySelector(`#feedbackTableBody tr.date-row[data-date="${date}"]`);
              if (dateRow) toggleRows(dateRow);
          });
      }
  }
});
}

setInterval(actualizarTabla, 10000);
