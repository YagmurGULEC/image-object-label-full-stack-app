
var forms = document.querySelectorAll('.needs-validation')
var upload = document.getElementById('upload-file')

Array.prototype.slice.call(forms)
    .forEach(function (form) {
      form.addEventListener('submit', function (event) {
       
        if (!form.checkValidity()) {
          event.preventDefault()
          event.stopPropagation()
        }
        if (upload) {
          if (upload.files.length == 0) {
            event.preventDefault()
            event.stopPropagation()
            alert('Please upload a file')
          }
        }
        form.classList.add('was-validated')


      }, false)
    })
