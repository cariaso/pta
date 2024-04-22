import pdb
import click
import qrcode
import qrcode.image.svg


@click.command()
def cli():
    """make qr"""

    todo = {
        'swing':'https://docs.google.com/document/d/1j_79xhfp8FyRPOBVsaCryDweY-2bdxowyJIIjShL7nE',
            'join':'https://somersetelementary.memberhub.com/join/c77fa1',
            'pay':'https://somersetelementary.memberhub.com/store',
            'main':'https://somersetelementary.memberhub.com/',
            }
    for label, url in todo.items():

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            # error_correction=qrcode.constants.ERROR_CORRECT_M,
            # error_correction=qrcode.constants.ERROR_CORRECT_Q,
            # error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=40,
            border=1,
        )

        body = url
        qr.add_data(body)
        qr.make(fit=True)

        #factory = qrcode.image.svg.SvgImage
        factory = qrcode.image.pil.PilImage
        #factory = qrcode.image.pure.PyPNGImage
        # factory = qrcode.image.svg.SvgFragmentImage
        # factory = qrcode.image.svg.SvgPathImage

        img = qr.make_image(
            #fill_color="green",
            #back_color="purple",
            image_factory=factory,
        )
        img.save(f"img-{label}-minimal.png")
        #img.save(f"img-{label}-minimal.svg")

if __name__ == '__main__':
    cli()
