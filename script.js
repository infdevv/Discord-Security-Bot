


// Onload
window.onload = () => {
    // Read JSON file locally
    fetch('stats.json')
        .then(response => response.json())
        .then(data => {
            document.getElementById('actions').innerHTML = data.actions;
            document.getElementById('nukes-stopped').innerHTML = data.nukes_stopped;
        })
        .catch(error => console.error(error));
}
