toastr.options.closeButton = true;

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        let cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Active dashboard sidebar
if (typeof activeDashboardSidebar !== 'undefined') {
    $('#dashboard-sidebar-main').find(`[data-sidebar='${activeDashboardSidebar}']`).addClass('active');
}

// Charts
function charts_number_format(number, decimals, dec_point, thousands_sep) {
  // *     example: number_format(1234.56, 2, ',', ' ');
  // *     return: '1 234,56'
  number = (number + '').replace(',', '').replace(' ', '');
  var n = !isFinite(+number) ? 0 : +number,
    prec = !isFinite(+decimals) ? 0 : Math.abs(decimals),
    sep = (typeof thousands_sep === 'undefined') ? ',' : thousands_sep,
    dec = (typeof dec_point === 'undefined') ? '.' : dec_point,
    s = '',
    toFixedFix = function(n, prec) {
      var k = Math.pow(10, prec);
      return '' + Math.round(n * k) / k;
    };
  // Fix for IE parseFloat(0.55).toFixed(0) = 0;
  s = (prec ? toFixedFix(n, prec) : '' + Math.round(n)).split('.');
  if (s[0].length > 3) {
    s[0] = s[0].replace(/\B(?=(?:\d{3})+(?!\d))/g, sep);
  }
  if ((s[1] || '').length < prec) {
    s[1] = s[1] || '';
    s[1] += new Array(prec - s[1].length + 1).join('0');
  }
  return s.join(dec);
}

function drawLineChart(data, elem, lbl, labels) {

    return new Chart(elem.getContext('2d'), {
        type: 'line',
        // The data for our dataset
        data: {
            labels: labels,
            // Information about the dataset
            datasets: [{
                label: lbl,
                backgroundColor: 'rgba(120, 84, 247, 0.1)',
                borderColor: '#7854F7',
                borderWidth: "1",
                data: data,
                pointRadius: 4,
                pointHoverRadius:5,
                pointHitRadius: 8,
                pointBackgroundColor: "#fff",
                pointHoverBackgroundColor: "#fff",
                pointBorderWidth: "1",
                borderCapStyle: 'butt',
                borderDash: [],
                borderDashOffset: 0.0,
                borderJoinStyle: 'miter',
            }]
        },
        // Configuration options
        options: {
            layout: {
              left: 0,
        right: 0,
        top: 0,
        bottom: 0
            },

            legend: { display: false },
            title:  { display: false },

            scales: {
                yAxes: [{
                    ticks: {
                        min: 0,
                        max: Math.max(...data),
                        maxTicksLimit: 5,
                        padding: 10,
                        // Include a dollar sign in the ticks
                        callback: function(value, index, values) {
                            return charts_number_format(value);
                        }
                    },
                    scaleLabel: {
                        display: false
                    },
                    gridLines: {
                         borderDash: [6, 10],
                         color: "#d8d8d8",
                         lineWidth: 1,
                    },
                }],
                xAxes: [{
                    gridLines: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        maxTicksLimit: labels.length
                    },
                    maxBarThickness: 25,
                }],
            },

            tooltips: {
                backgroundColor: '#333',
                titleFontSize: 13,
                titleFontColor: '#fff',
                bodyFontColor: '#fff',
                bodyFontSize: 13,
                displayColors: false,
                xPadding: 10,
                yPadding: 10,
                intersect: false,
                callbacks: {
                    label: function(tooltipItem, chart) {
                        let datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
                        return datasetLabel + ': ' + 'Ksh.' + ' ' + tooltipItem.yLabel;
                    }
                }
            }
        },
    })
}

function drawPieChart(canvasElem, data, labels, bgColors, bgHoverColors, hoverBorderColor) {
    return new Chart(canvasElem, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: bgColors,
                hoverBackgroundColor: bgHoverColors,
                hoverBorderColor: hoverBorderColor,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            tooltips: {
                backgroundColor: "#333",
                bodyFontColor: "#fff",
                borderColor: '#333',
                borderWidth: 1,
                xPadding: 15,
                yPadding: 15,
                displayColors: false,
                caretPadding: 10,
            },
            legend: {
                display: false
            },
        },
    });
}

// Progress bars
$('.income-breakdown-progress-circle').each(function () {
    let percent = parseFloat($(this).data('percent'));
    let text = $(this).data('text');
    let color = $(this).data('color');
    let fraction = percent / 100;

    let bar = new ProgressBar.Circle(this, {
        color: color,
        strokeWidth: 5,
        trailWidth: 2,
        duration: 1200,
        text: {
            value: '0 %'
        }
    });

    bar.setText(text);
    bar.animate(fraction, {
        duration: 800
    });
})

$('.clipboard-copy').on('click', function (event) {
    event.preventDefault();
    let content = $(this).data('content');
    let tempInput = document.createElement("input");
	tempInput.setAttribute('style', 'position: absolute; left: -1000px; top: -1000px');
	tempInput.value = content;
	document.body.appendChild(tempInput);
	tempInput.select();
	document.execCommand("copy");
	document.body.removeChild(tempInput);

	toastr.info('Copied to clipboard', 'Info!');
})

/*--------------------------------------------------*/
/*  Interactive Effects
/*--------------------------------------------------*/
$(".radio").each(function() {
    var intElem = $(this);
    intElem.on('click', function() {
        intElem.addClass('interactive-effect');
       setTimeout(function() {
                intElem.removeClass('interactive-effect');
       }, 400);
    });
});

// Create timer
function createTimer(countDownDate, container, callback) {

	countDownDate = new Date(countDownDate).getTime();

	// Update the count down every 1 second
	let x = setInterval(function () {
	// Get today's date and time
	let now = new Date().getTime();

	// Find the distance between now and the count down date
	let distance = countDownDate - now;
	// Time calculations for days, hours, minutes and seconds
	let days = Math.floor(distance / (1000 * 60 * 60 * 24));
	let hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
	let minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
	let seconds = Math.floor((distance % (1000 * 60)) / 1000);

	$(container).find('.days').text(days + "d");
	$(container).find('.hours').text(hours + "h");
	$(container).find('.minutes').text(minutes + "m");
	$(container).find('.seconds').text(seconds + "s");

		// If the count down is finished, execute callback function
		if (distance < 0) {
			clearInterval(x);
			callback();
		}
	}, 1000);
	return x;
}

// To local datetime
function toLocalDateTime() {
    $('.to_local_datetime').each(function(i, obj) {
        let utc_datetime = moment.utc($(this).data('utc'));
        let local_datetime = moment(utc_datetime).local();
        local_datetime = local_datetime.format("MMM. DD, YYYY, hh:mm a");
        $(this).text(local_datetime);
    });
}

// To local date
function toLocalDate() {
    $('.to_local_date').each(function(i, obj) {
        let utc_date = moment.utc($(this).data('utcdate'));
        let local_date = moment(utc_date).local();
        local_date = local_date.format("MMM. DD, YYYY");
        $(this).text(local_date);
    });
}

$(document).ready(function () {
    toLocalDateTime();
    toLocalDate();
})

// Link trigger
$('.link-trigger').on('click', function (event) {
    event.preventDefault();
    location.href = $(this).data('url');
})

function showFormErrors(errors, formID) {
    for (let key in errors) {
        if (errors.hasOwnProperty(key)) {
            let errorEl = $(`#${formID} [data-label=${key}]`);
            errorEl.css('display', 'block');
            for (let i = 0; i < errors[key].length ; i++) {
                let errorsLi = document.createElement('li');
                errorsLi.innerText = errors[key][i];
                errorEl.append(errorsLi);
            }
        }
    }
}

function hideFormErrors(form) {
    let formErrors = form.querySelectorAll('.form-errors');
    for (let i = 0; i < formErrors.length; i++) {
        $(formErrors[i]).css('display', 'none');
        $(formErrors[i]).html('');
    }
}

tippy('[data-tippy-placement]', {
    duration: 0,
    arrow: true,
});

// More description
let moreDesc = document.querySelectorAll('.more-desc');
for (let i = 0; i < moreDesc.length; i++) {
    new bootstrap.Popover(
        moreDesc[i],
        {
            content: $(moreDesc[i]).data('desc'),
            html: true,
            title: $(moreDesc[i]).data('title'),
            trigger: 'hover'
        }
    )
}

// Login required
$('.login-required').on('click', function (event) {
    event.preventDefault();
    let next_url = $(this).data('url');
    let msg = $(this).data('msg');
    location.href = `/accounts/login-required/?msg=${msg}&next=${next_url}`;
})

/*--------------------------------------------------*/
/*  Star Rating
/*--------------------------------------------------*/
function starRating(ratingElem) {

    $(ratingElem).each(function() {

        var dataRating = $(this).attr('data-rating');

        // Rating Stars Output
        function starsOutput(firstStar, secondStar, thirdStar, fourthStar, fifthStar) {
            return(''+
                '<span class="'+firstStar+'"></span>'+
                '<span class="'+secondStar+'"></span>'+
                '<span class="'+thirdStar+'"></span>'+
                '<span class="'+fourthStar+'"></span>'+
                '<span class="'+fifthStar+'"></span>');
        }

        var fiveStars = starsOutput('star','star','star','star','star');

        var fourHalfStars = starsOutput('star','star','star','star','star half');
        var fourStars = starsOutput('star','star','star','star','star empty');

        var threeHalfStars = starsOutput('star','star','star','star half','star empty');
        var threeStars = starsOutput('star','star','star','star empty','star empty');

        var twoHalfStars = starsOutput('star','star','star half','star empty','star empty');
        var twoStars = starsOutput('star','star','star empty','star empty','star empty');

        var oneHalfStar = starsOutput('star','star half','star empty','star empty','star empty');
        var oneStar = starsOutput('star','star empty','star empty','star empty','star empty');
        var halfStar = starsOutput('star half','star empty','star empty','star empty','star empty');
        var zeroStar = starsOutput('star empty','star empty','star empty','star empty','star empty');

        // Rules
        if (dataRating >= 4.75) {
            $(this).append(fiveStars);
        } else if (dataRating >= 4.25) {
            $(this).append(fourHalfStars);
        } else if (dataRating >= 3.75) {
            $(this).append(fourStars);
        } else if (dataRating >= 3.25) {
            $(this).append(threeHalfStars);
        } else if (dataRating >= 2.75) {
            $(this).append(threeStars);
        } else if (dataRating >= 2.25) {
            $(this).append(twoHalfStars);
        } else if (dataRating >= 1.75) {
            $(this).append(twoStars);
        } else if (dataRating >= 1.25) {
            $(this).append(oneHalfStar);
        } else if (dataRating >= 0.75) {
            $(this).append(oneStar);
        } else if (dataRating >= 0.25) {
            $(this).append(halfStar);
        } else {
            $(this).append(zeroStar);
        }
    });
}

$(document).ready(function () {
    starRating('.star-rating');
})

// Add to cart
$('.add-to-cart').on('click', function (event) {
    event.preventDefault();
    let ebook = $(this).data('ebook');
    let affiliate = $(this).data('affiliate');
    $.ajax({
        type: 'POST',
        url: '/accounts/cart/add/',
        data: {
            'csrfmiddlewaretoken': getCookie('csrftoken'),
            'ebook': ebook, 'affiliate': affiliate
        },
        success: function (data) {
            toastr.success('Item added to cart.', 'Success!');
            $('.cart-items').text(data['cart_items']);
        },
        error: function (data) {
            data = data.responseJSON;
            if (data) {
                if (data.hasOwnProperty('message')) {
                    if (data['message'] === 'exists') {
                        toastr.info('Cart item already exists.', 'Info!');
                    }
                }
            } else {
                toastr.error('Unable to process request. Please try again.', 'Error!');
            }
        }
    })
})

// Make rating
function makeRating(elemID, value) {
    // Current and below active
    for (let i = 0; i < value; i++) {
        $(`#${elemID} [data-value=${i + 1}]`).addClass('active');
    }
    // Above inactive
    for (let i = 5; i > value; i--) {
        $(`#${elemID} [data-value=${i}]`).removeClass('active');
    }
}

/* Attention */
function showAttention() {
    $('.attention').addClass('shown');
    $('#fixed-bottom-overlay').addClass('d-none');
}

function hideAttention() {
    $('.attention').removeClass('shown');
    $('#fixed-bottom-overlay').removeClass('d-none');
}
$(document).ready(function () {
    if (document.querySelector(".attention")) {
        setTimeout(showAttention, 2000);
    }
})

$('.attention .close-btn').on('click', function (event) {
    event.preventDefault();
    hideAttention();
})

// CKEditor
function createCKEditor(elem, plugins, ) {
    return CKSource.Editor.create(elem, {
        extraPlugins: plugins,
        autosave: {
            save(editor) {
                // The saveData() function must return a promise
                // which should be resolved when the data is successfully saved.
                return saveData(editor.getData());
            },
            waitingTime: 0
        },
        mediaEmbed: {previewsInData: true},

        toolbar: {
            items: [
                'bold',
                'italic',
                'blockQuote',
                'link',
                'heading',
                'imageUpload',
                'imageInsert',
                'indent',
                'outdent',
                'numberedList',
                'bulletedList',
                'mediaEmbed',
                'insertTable',
                'alignment',
                'codeBlock',
                'findAndReplace',
                'fontBackgroundColor',
                'fontColor',
                'fontFamily',
                'fontSize',
                'horizontalLine',
                'removeFormat',
                'strikethrough',
                'subscript',
                'superscript',
                'underline',
                'undo',
                'redo'
            ]
        },
        language: 'en',
        blockToolbar: [
            'bold',
                'italic',
                'blockQuote',
                'link',
                'heading',
                'imageUpload',
                'imageInsert',
                'indent',
                'outdent',
                'numberedList',
                'bulletedList',
                'mediaEmbed',
                'insertTable',
                'alignment',
                'codeBlock',
                'findAndReplace',
                'fontBackgroundColor',
                'fontColor',
                'fontFamily',
                'fontSize',
                'horizontalLine',
                'removeFormat',
                'strikethrough',
                'subscript',
                'superscript',
                'underline',
                'undo',
                'redo'
        ],
        image: {
            toolbar: [
                'imageTextAlternative',
                'imageStyle:full',
                'imageStyle:side',
                'linkImage'
            ]
        },
        table: {
            contentToolbar: [
                'tableColumn',
                'tableRow',
                'mergeTableCells',
                'tableCellProperties',
                'tableProperties'
            ]
        },
        licenseKey: '',

    }).then(newEditor => {
        editor = newEditor;
    })
}

// Flutterwave
function makeFwPayment(event) {
    FlutterwaveCheckout({
        public_key: event['public_key'],
        tx_ref: event['trans_id'],
        amount: event['amount'],
        currency: event['currency'],
        country: event['country'],
        payment_options: "",
        redirect_url: event['redirect_url'],
        customer: {
            email: event['email'],
            phone_number: event['phone_number'],
        },
        callback: function (data) {
            //
        },
        onclose: function() {
            // close modal
            toastr.error('Payment session terminated.', 'Error!');
        },
        customizations: {
            title: event['site_name'],
            description: "Payment for account deposit",
            logo: "https://www.easyearn.co.ke/static/images/favicon.png",
        },
    });
}
