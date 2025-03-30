document.addEventListener('DOMContentLoaded', function() {
  // Username Update
  $('#usernameForm').submit(function(e) {
      e.preventDefault();
      const btn = $(this).find('button');
      btn.html('<span class="spinner-border spinner-border-sm" role="status"></span> Updating...');
      
      $.ajax({
          url: '/api/update-username',
          method: 'POST',
          contentType: 'application/json',
          data: JSON.stringify({
              username: $('#usernameInput').val()
          }),
          success: function(data) {
              if(data.success) {
                  showFeedback('#usernameFeedback', 'Username updated successfully!', 'success');
              } else {
                  showFeedback('#usernameFeedback', data.error, 'danger');
              }
          },
          complete: function() {
              btn.html('Update');
          }
      });
  });

  // Password Update
  $('#passwordForm').submit(function(e) {
      e.preventDefault();
      const formData = {
        current_password: $('#passwordForm input[name="current_password"]').val(),
        new_password: $('#passwordForm input[name="new_password"]').val(),
        confirm_password: $('#passwordForm input[name="confirm_password"]').val()
    };
    
    // Add client-side validation
    if(formData.new_password !== formData.confirm_password) {
        showFeedback('#passwordFeedback', 'New passwords do not match', 'danger');
        return;
    }
    
    if(formData.new_password.length < 6) {
        showFeedback('#passwordFeedback', 'Password must be at least 6 characters', 'danger');
        return;
    }

      const btn = $(this).find('button');
      btn.html('<span class="spinner-border spinner-border-sm" role="status"></span> Updating...');

      $.ajax({
          url: '/api/update-password',
          method: 'POST',
          contentType: 'application/json',
          data: JSON.stringify(formData),
          success: function(data) {
              if(data.success) {
                  showFeedback('#passwordFeedback', 'Password updated successfully!', 'success');
                  $('#passwordForm')[0].reset();
              } else {
                  showFeedback('#passwordFeedback', data.error, 'danger');
              }
          },
          complete: function() {
              btn.html('Change Password');
          }
      });
  });

  // Avatar Upload
$('#avatarForm').submit(function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const btn = $(this).find('button');
    const fileInput = $('input[type="file"]')[0];
    
    // Validate file selection
    if (!fileInput.files || !fileInput.files[0]) {
        showFeedback('#avatarFeedback', 'Please select a file first', 'danger');
        return;
    }

    btn.html('<span class="spinner-border spinner-border-sm" role="status"></span> Uploading...');

    $.ajax({
        url: '/api/update-avatar',
        method: 'POST',
        data: formData,
        contentType: false,
        processData: false,
        success: function(data) {
            if(data.success) {
                // Force cache refresh
                $('#avatarPreview').attr('src', data.avatar_url + '?t=' + Date.now());
                $('#avatarModal').modal('hide');
                showToast('Profile picture updated!', 'success');
            } else {
                showFeedback('#avatarFeedback', data.error, 'danger');
            }
        },
        error: function(xhr) {
            showFeedback('#avatarFeedback', `Upload failed: ${xhr.statusText}`, 'danger');
        },
        complete: function() {
            btn.html('Upload New Photo');
        }
    });
});

  function showFeedback(selector, message, type) {
      const element = $(selector);
      element.html(`
          <div class="alert alert-${type} animate__animated animate__fadeIn">
              ${message}
          </div>
      `);
      setTimeout(() => element.empty(), 3000);
  }

  function showToast(message, type) {
      const toast = $(`
          <div class="toast align-items-center text-white bg-${type} border-0 position-fixed bottom-0 end-0 m-3">
              <div class="d-flex">
                  <div class="toast-body">${message}</div>
                  <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
              </div>
          </div>
      `);
      $('body').append(toast);
      new bootstrap.Toast(toast[0]).show();
  }


document.getElementById('avatarInput').addEventListener('change', function(e) {
    const fileName = e.target.files[0] ? e.target.files[0].name : 'No file chosen';
    document.getElementById('fileName').textContent = fileName;
});

});

