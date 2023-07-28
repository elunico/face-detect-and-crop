function selected(selectElt) {
  return selectElt.selectedOptions[0].value;
}

gobutton.onclick = function () { submit('zip'); };

batch.oninput = () => {
  console.log(batch.selectedOptions[0].value);
  if (batch.selectedOptions[0].value == "file") {
    gobutton.onclick = () => submit('file');
    image.accept = '.png,.jpg,.jpeg,.tiff';
  } else {
    gobutton.onclick = () => submit('zip');
    image.accept = '.zip';
  }
};

function doFetch(route, body) {
  fetch(route, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': body.length
    },
    body: body
  }).then(resp => {
    console.log(resp.status);
    if (resp.status == 421) {
      throw Error('No faces detected!');
    } else if (resp.status != 200) {
      throw Error("An error occurred");
    }
    return resp.blob();
  }).then(blob => {
    console.log(blob);
    let file = window.URL.createObjectURL(blob);
    console.log(file);
    downloader.href = file;
    downloader.download = 'boxed.zip';
    downloader.click();
  }).catch(err => {
    console.log(err);
    statusResponse.textContent = err;
  });
}
