
// function selected(selectElt) {
//   return selectElt.selectedOptions[0].value;
// }

// gobutton.onclick = function () { submit('zip'); };

// batch.oninput = () => {
//   console.log(batch.selectedOptions[0].value);
//   if (batch.selectedOptions[0].value == "file") {
//     gobutton.onclick = () => submit('file');
//     image.accept = '.png,.jpg,.jpeg,.tiff';
//   } else {
//     gobutton.onclick = () => submit('zip');
//     image.accept = '.zip';
//   }
// };

// function doFetch(route, body) {
//   fetch(route, {
//     method: 'POST',
//     headers: {
//       'Content-Type': 'application/json',
//       'Content-Length': body.length
//     },
//     body: body
//   }).then(resp => {
//     console.log(resp.status);
//     if (resp.status == 421) {
//       throw Error('No faces detected!');
//     } else if (resp.status != 200) {
//       throw Error("An error occurred");
//     }
//     return resp.blob();
//   }).then(blob => {
//     console.log(blob);
//     let file = window.URL.createObjectURL(blob);
//     console.log(file);
//     downloader.href = file;
//     downloader.download = 'boxed.zip';
//     downloader.click();
//   }).catch(err => {
//     console.log(err);
//     statusResponse.textContent = err;
//   });
// }

function submitOne() {
  console.log("Submitting one");
  if (image.files.length < 1) {
    alert("Must choose an image file");
    return;
  }
  let data = image.files[0];
  let reader = new FileReader();
  reader.readAsBinaryString(data);
  reader.addEventListener('load', ev => {
    let bdata = btoa(reader.result);
    let s = JSON.stringify({
      imagedata: bdata,
      maxfaces: maxfaces.value,
      minheight: minheight.value,
      minwidth: minwidth.value,
      operation: selected(operation),
      multiplier: selected(multiplier),
      mimetype: data.type,
      filename: data.name
    });

    doFetch('/detect', s);
  });

}

function submitZip() {
  console.log("Submitting one");

  if (image.files.length < 1) {
    alert("Must choose a zip file");
    return;
  }
  let data = image.files[0];
  let reader = new FileReader();
  reader.readAsBinaryString(data);
  reader.addEventListener('load', ev => {
    let bdata = btoa(reader.result);
    let s = JSON.stringify({
      imagedata: bdata,
      maxfaces: maxfaces.value,
      minheight: minheight.value,
      minwidth: minwidth.value,
      operation: selected(operation),
      multiplier: selected(multiplier),
      mimetype: data.type,
      filename: data.name
    });

    doFetch('/detectall', s);
  });
}

function submit(type) {
  statusResponse.textContent = '';
  if (type == 'zip') {
    console.log('submitting zip');
    submitZip();
  } else {
    console.log('submitting one');
    submitOne();
  }

}
