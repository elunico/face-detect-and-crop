
operation.oninput = () => {
  let op = selected(operation);
  if (op.indexOf('resize') >= 0) {
    step6Box.removeAttribute('hidden');
  } else {
    step6Box.setAttribute('hidden', true);
  }
};

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

    doFetch('/do-detect', s);
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

    doFetch('/do-detectall', s);
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
